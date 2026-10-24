"""Offline hosted-composition/max-image probe using fictional configuration only."""
import argparse
from contextlib import ExitStack
import gc
from io import BytesIO
import json
from pathlib import Path
import platform
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from profile_v1_models import memory_mib


def profile(args):
    if args.runtime_dir:
        sys.path.insert(0, str(args.runtime_dir.resolve()))
    from PIL import Image
    from hosted_api import create_app
    import v1_lite_models as adapter_module
    from v1_lite_models import LiteBinaryRuntime
    from v1_uploads import normalize_image

    # Never read .env or production configuration. Guards also fail the probe if
    # composition unexpectedly attempts HTTP, S3 or a PostgreSQL connection.
    config = {'GRAPHISCAN_V1_BACKEND': 'supabase-postgres',
        'GRAPHISCAN_V1_SUPABASE_URL': 'https://fixture.example.invalid',
        'GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY': 'sb_publishable_fixture_only',
        'GRAPHISCAN_V1_DATABASE_URL': 'postgresql://graphiscan_api_reader:fixture@db.example.invalid/test',
        'GRAPHISCAN_V1_PASSWORD_DATABASE_URL': 'postgresql://graphiscan_password_writer:fixture@db.example.invalid/test',
        'GRAPHISCAN_V1_ADMIN_DATABASE_URL': 'postgresql://graphiscan_admin_writer:fixture@db.example.invalid/test',
        'GRAPHISCAN_V1_CURSOR_SECRET': 'ab'*32,
        'GRAPHISCAN_CORS_ALLOWED_ORIGINS': 'https://admin.example.invalid',
        'GRAPHISCAN_REQUIRE_MODEL': 'true',
        'GRAPHISCAN_V1_MODEL_MANIFEST': str(args.manifest.resolve()),
        'GRAPHISCAN_V1_STORAGE_BUCKET': 'fixture-private',
        'GRAPHISCAN_V1_S3_ENDPOINT': 'https://fixture.example.invalid/storage/v1/s3',
        'GRAPHISCAN_V1_S3_REGION': 'us-east-1',
        'GRAPHISCAN_V1_S3_ACCESS_KEY_ID': 'fixture', 'GRAPHISCAN_V1_S3_SECRET_ACCESS_KEY': 'fixture'}
    targets = ['psycopg.connect', 'requests.sessions.Session.request', 'botocore.client.BaseClient._make_api_call']
    with ExitStack() as stack:
        guards = [stack.enter_context(patch(target, side_effect=AssertionError('External access disabled'))) for target in targets]
        if args.builtin_resnet_experiment:
            from ai_edge_litert.compiled_model import CompiledModel, CpuKernelMode, CpuOptions, HardwareAccelerator, Options
            original_factory = CompiledModel.from_file
            def factory(path, hardware_accel=None, **options):
                if Path(path).name.startswith('resnet50-'):
                    return original_factory(path, options=Options(hardware_accelerators=HardwareAccelerator.CPU,
                        cpu_options=CpuOptions(num_threads=1, kernel_mode=CpuKernelMode.BUILTIN)))
                return original_factory(path, hardware_accel, **options)
            stack.enter_context(patch.object(CompiledModel, 'from_file', side_effect=factory))
        app = create_app(config)
        runtime = app.extensions['graphiscan_v1_backend'].screening_upload_service.runtime
        if not isinstance(runtime, LiteBinaryRuntime):
            raise ValueError('Expected lightweight hosted composition')
        client = app.test_client()
        if client.get('/api/v1/health').status_code != 200 or client.get('/api/v1/models').status_code != 401:
            raise ValueError('Unexpected API boundary')
        payload = BytesIO()
        if args.pattern == 'four-tone-noise':
            import numpy as np
            image = Image.fromarray(np.random.default_rng(20261023).integers(0, 4, (4000, 4000), dtype=np.uint8)*85).convert('RGB')
        else:
            image = Image.new('RGB', (4000, 4000), 'white')
        with image:
            image.save(payload, format='PNG')
        raw = payload.getvalue()
        del image, payload
        gc.collect()
        report = {'status': 'profiling', 'platform': platform.system(), 'sample': f'generated-{args.pattern}-16-megapixels',
                  'generated_png_bytes': len(raw),
                  'resnet_cpu_kernel': 'builtin-experiment' if args.builtin_resnet_experiment else getattr(adapter_module, 'RESNET_CPU_KERNEL', 'default-delegate'),
                  'composition': 'real-hosted-api-with-fictional-configuration', 'baseline': memory_mib(), 'models': [],
                  'limitations': ['Local validation, not a deployed or authenticated hosted workflow.',
                                 'External calls disabled; no live Auth/SQL/Storage latency or buffers measured.',
                                 'Sequential requests; use one Gunicorn worker and one thread for this candidate.']}
        # Repeating ResNet50 checks normalization while the largest model is
        # already resident, then returning to MobileNetV2 checks cache release.
        for key in ('mobilenetv2', 'efficientnetb0', 'resnet50', 'resnet50', 'mobilenetv2'):
            started = time.perf_counter()
            normalized = normalize_image(BytesIO(raw))
            identity = {**runtime.entries[key][0], 'task_type': 'binary'}
            runtime.infer(normalized, identity)
            report['models'].append({'model_key': key, 'normalize_and_infer_seconds': round(time.perf_counter()-started, 3),
                                     'cached_model_count': len(runtime.networks), 'memory': memory_mib()})
            print(json.dumps({'status': 'hosted-lite-profiled', **report['models'][-1]}), flush=True)
        if any(guard.called for guard in guards) or 'tensorflow' in sys.modules:
            raise RuntimeError('Unexpected external call or TensorFlow import')
        report.update(status='profile-complete', tensorflow_imported=False, external_calls=0, final_memory=memory_mib())
        return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'model/deployment.litert.local.json')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--pattern', choices=['white', 'four-tone-noise'], default='white')
    parser.add_argument('--builtin-resnet-experiment', action='store_true', help='Experiment only: select builtin CPU kernels for ResNet50; does not change the serving adapter.')
    args = parser.parse_args()
    try:
        report = profile(args)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(report), flush=True)
    except Exception as failure:
        print(json.dumps({'status': 'hosted-lite-profile-not-confirmed', 'error_type': type(failure).__name__}), flush=True)
        sys.exit(1)
