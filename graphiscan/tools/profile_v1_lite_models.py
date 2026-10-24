"""Profile parity-checked FP32 copies in a process that never imports TensorFlow."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from profile_v1_models import memory_mib


def profile(args):
    if args.runtime_dir:
        sys.path.insert(0, str(args.runtime_dir.resolve()))
    import numpy as np
    from PIL import Image
    from ai_edge_litert.compiled_model import CompiledModel, HardwareAccelerator
    from v1_uploads import file_digest, normalize_image

    comparison = json.loads((args.artifact_dir / 'comparison.local.json').read_text(encoding='utf-8'))
    if comparison.get('status') != 'parity-passed' or comparison.get('split') != 'existing-binary-test':
        raise ValueError('Require a completed test-split parity report')
    adapter = None
    if args.manifest:
        from v1_lite_models import LiteBinaryRuntime
        adapter = LiteBinaryRuntime(args.manifest)
    source = BytesIO()
    Image.new('RGB', (224, 224), 'white').save(source, format='PNG')
    source.seek(0)
    sample = normalize_image(source)
    pixels = np.array(Image.open(BytesIO(sample)).convert('RGB').resize((224, 224))).astype('float32')[None]
    report = {'status': 'profiling', 'runtime': 'litert-compiled-model-cpu',
              'platform': platform.system(), 'sample': 'generated-white-image-only',
              'baseline': memory_mib(), 'models': [], 'database_accessed': False,
              'limitations': ['Local process metrics, not Linux container or hosted measurements.',
                              'No Auth/database/Storage/concurrent upload overhead measured.']}
    report['cache_policy'] = 'single-model-adapter' if adapter else 'all-models-cached'
    caches = []
    rows = comparison['models'] + ([comparison['models'][0]] if adapter else [])
    for row in rows:
        key, source_hash = row['model_key'], row['source_artifact_sha256']
        if key not in {'mobilenetv2', 'efficientnetb0', 'resnet50'} or not row['parity_passed']:
            raise ValueError('Unsupported/unverified deployment copy')
        import re
        if not re.fullmatch('[a-f0-9]{64}', source_hash):
            raise ValueError('Invalid source identity')
        artifact = args.artifact_dir / f'{key}-{source_hash}-fp32.tflite'
        if file_digest(artifact) != row['converted_artifact_sha256']:
            raise ValueError('Deployment copy identity mismatch')
        if adapter:
            entry = adapter.entries[key][0]
            if entry['artifact_sha256'] != row['converted_artifact_sha256']:
                raise ValueError('Adapter deployment identity mismatch')
            model_identity = {**entry, 'task_type': 'binary'}
            started = time.perf_counter()
            adapter.infer(sample, model_identity)
            cold = time.perf_counter() - started
            started = time.perf_counter()
            adapter.infer(sample, model_identity)
            warm = time.perf_counter() - started
            cache_count = len(adapter.networks)
        else:
            started = time.perf_counter()
            model = CompiledModel.from_file(str(artifact), HardwareAccelerator.CPU)
            inputs, outputs = model.create_input_buffers(0), model.create_output_buffers(0)
            inputs[0].write(pixels)
            model.run_by_index(0, inputs, outputs)
            outputs[0].read(1, np.float32)
            cold = time.perf_counter() - started
            started = time.perf_counter()
            model.run_by_index(0, inputs, outputs)
            outputs[0].read(1, np.float32)
            warm = time.perf_counter() - started
            caches.append((model, inputs, outputs))
            cache_count = len(caches)
        item = {'model_key': key, 'first_inference_seconds': round(cold, 3),
                'warm_inference_seconds': round(warm, 3),
                'cached_model_count': cache_count, 'memory': memory_mib()}
        report['models'].append(item)
        print(json.dumps({'status': 'lite-model-profiled', **item}), flush=True)
    if 'tensorflow' in sys.modules:
        raise RuntimeError('TensorFlow was unexpectedly imported')
    report.update(status='profile-complete', tensorflow_imported=False, final_memory=memory_mib())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path)
    parser.add_argument('--artifact-dir', type=Path, default=ROOT.parent / '.local-tools/lite-model-experiment')
    parser.add_argument('--manifest', type=Path, help='Profile the single-cache versioned adapter, including a return model switch.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = profile(args)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(report), flush=True)
    except Exception as failure:
        print(json.dumps({'status': 'lite-profile-not-confirmed', 'error_type': type(failure).__name__}), flush=True)
        sys.exit(1)
