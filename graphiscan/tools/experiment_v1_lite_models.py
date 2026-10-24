"""Offline FP32 deployment-copy experiment; never publishes or changes live artifacts."""
import argparse
from contextlib import redirect_stdout
import gc
import hashlib
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def samples(compare):
    import numpy as np
    import predict
    from PIL import Image, ImageDraw
    from v1_uploads import normalize_image
    source = []
    if compare:
        for label, name in enumerate(('normal', 'high_potential')):
            directory = ROOT / 'binary_dataset/test' / name
            for path in sorted(directory.iterdir()):
                if path.is_file() and path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                    raw = path.read_bytes()
                    source.append((label, hashlib.sha256(raw).hexdigest(), raw))
    else:
        image = Image.new('RGB', (224, 224), 'white')
        draw = ImageDraw.Draw(image)
        for y in (64, 112, 160):
            draw.line([(32, y), (64, y-15), (96, y+10), (128, y-10), (176, y)], fill='black', width=3)
        buffer = BytesIO(); image.save(buffer, format='PNG')
        source.append((0, hashlib.sha256(buffer.getvalue()).hexdigest(), buffer.getvalue()))
    if not source:
        raise ValueError('No samples available')
    digest = hashlib.sha256()
    for label, content_hash, _ in sorted(source, key=lambda row: (row[0], row[1])):
        digest.update(f'{label}:{content_hash}\n'.encode())
    arrays = []
    with TemporaryDirectory(prefix='graphiscan-lite-check-') as folder:
        for index, (_, _, raw) in enumerate(source):
            target = Path(folder) / f'{index}.png'
            target.write_bytes(normalize_image(BytesIO(raw)))
            arrays.append(predict.prepare_image(str(target)))
    return np.concatenate(arrays), [row[0] for row in source], digest.hexdigest()


def matrix(labels, scores):
    result = [[0, 0], [0, 0]]
    for label, score in zip(labels, scores):
        result[label][int(score >= .75)] += 1
    return result


def experiment(args):
    if args.verify_existing and args.verify_existing.resolve() == args.output_dir.resolve():
        raise ValueError('Existing-copy verification needs a separate report directory')
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
    os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
    os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '2')
    os.environ.setdefault('TF_NUM_INTEROP_THREADS', '1')
    if args.runtime_dir:
        sys.path.insert(0, str(args.runtime_dir.resolve()))
    import numpy as np
    import predict
    from ai_edge_litert.compiled_model import CompiledModel, CpuKernelMode, CpuOptions, HardwareAccelerator, Options
    from v1_models import VersionedBinaryRuntime
    from v1_uploads import file_digest

    print(json.dumps({'status': 'preparing-samples', 'existing_test_split': args.compare}), flush=True)
    runtime = VersionedBinaryRuntime(ROOT / 'model/deployment.local.json')
    keys = args.model or sorted(runtime.entries, key=lambda key: (key != 'mobilenetv2', key))
    pixels, labels, dataset_hash = samples(args.compare)
    existing = None
    if args.verify_existing:
        existing = json.loads((args.verify_existing / 'comparison.local.json').read_text(encoding='utf-8'))
        if (existing.get('status') != 'parity-passed' or existing.get('dataset_sha256') != dataset_hash
                or existing.get('sample_count') != len(labels) or existing.get('quantization') != 'none-float32'):
            raise ValueError('Require completed parity evidence for the same samples')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {'status': 'experiment-running', 'quantization': 'none-float32',
              'platform': platform.system(), 'conversion_performed': not bool(args.verify_existing),
              'resnet_cpu_kernel': args.resnet_cpu_kernel,
              'sample_count': len(labels), 'split': 'existing-binary-test' if args.compare else 'generated-only',
              'dataset_sha256': dataset_hash, 'decision_threshold': .75,
              'score_tolerance': .0001, 'models': [], 'database_accessed': False,
              'registry_published': False, 'live_artifacts_changed': False,
              'limitations': ['Deployment-copy experiment, not independent or clinical validation.',
                              'Numerical comparison only; no serving memory-limit or authenticated hosted workflow verification.']}
    for key in keys:
        entry, artifact = runtime.entries[key]
        started = time.perf_counter()
        print(json.dumps({'status': 'loading-reference', 'model_key': key}), flush=True)
        network = predict.load_model(str(artifact), compile=False, safe_mode=False,
                                    custom_objects={'preprocess_input': predict.resnet50_preprocess_input})
        if tuple(network.input_shape) != (None, 224, 224, 3) or tuple(network.output_shape) != (None, 1):
            raise ValueError('Unsupported reference shape')
        reference = np.asarray(network.predict(pixels, batch_size=1, verbose=0)).reshape(-1)
        target = (args.verify_existing or args.output_dir) / f'{key}-{entry["artifact_sha256"]}-fp32.tflite'
        if existing:
            verified = next(row for row in existing['models'] if row['model_key'] == key)
            if (verified.get('parity_passed') is not True or verified['source_artifact_sha256'] != entry['artifact_sha256']
                    or file_digest(target) != verified['converted_artifact_sha256']):
                raise ValueError('Existing deployment copy identity mismatch')
        else:
            print(json.dumps({'status': 'converting-float32', 'model_key': key}), flush=True)
            with TemporaryDirectory(prefix='graphiscan-lite-export-') as folder, redirect_stdout(StringIO()):
                # Model.predict uses training=False. Trace it explicitly so training-only
                # random augmentation and dropout cannot enter the deployment graph.
                export = predict.tf.Module()
                # Track raw variables instead of the Keras object: serializing that
                # object also walks cached training functions and augmentation state.
                export.weights = [variable.value for variable in network.variables]
                @predict.tf.function(input_signature=[predict.tf.TensorSpec((1, 224, 224, 3), predict.tf.float32, name='pixels')])
                def serve(pixels):
                    return {'probability': network(pixels, training=False)}
                predict.tf.saved_model.save(export, folder, signatures={'serving_default': serve})
                converter = predict.tf.lite.TFLiteConverter.from_saved_model(folder)
                converter.target_spec.supported_ops = [predict.tf.lite.OpsSet.TFLITE_BUILTINS]
                converter.optimizations = []
                target.write_bytes(converter.convert())
        if key == 'resnet50' and args.resnet_cpu_kernel == 'builtin':
            compiled = CompiledModel.from_file(str(target), options=Options(
                hardware_accelerators=HardwareAccelerator.CPU,
                cpu_options=CpuOptions(num_threads=1, kernel_mode=CpuKernelMode.BUILTIN)))
        else:
            compiled = CompiledModel.from_file(str(target), HardwareAccelerator.CPU)
        inputs, outputs = compiled.create_input_buffers(0), compiled.create_output_buffers(0)
        converted = []
        for row in pixels:
            inputs[0].write(np.ascontiguousarray(row[None], dtype=np.float32))
            compiled.run_by_index(0, inputs, outputs)
            converted.append(float(outputs[0].read(1, np.float32)[0]))
        converted = np.asarray(converted)
        if not np.isfinite(reference).all() or not np.isfinite(converted).all():
            raise ValueError('Nonfinite output')
        disagreement = int(np.count_nonzero((reference >= .75) != (converted >= .75)))
        maximum_error = float(np.max(np.abs(reference - converted)))
        item = {'model_key': key, 'source_artifact_sha256': entry['artifact_sha256'],
                'converted_artifact_sha256': file_digest(target),
                'converted_mib': round(target.stat().st_size / 2**20, 2),
                'max_absolute_score_error': maximum_error,
                'classification_disagreements': disagreement,
                'reference_confusion_matrix': matrix(labels, reference) if args.compare else None,
                'converted_confusion_matrix': matrix(labels, converted) if args.compare else None,
                'parity_passed': disagreement == 0 and maximum_error <= .0001,
                'elapsed_seconds': round(time.perf_counter()-started, 2)}
        report['models'].append(item)
        print(json.dumps({'status': 'deployment-copy-checked', **item}), flush=True)
        (args.output_dir / 'comparison.local.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        del compiled, inputs, outputs, network
        if not args.verify_existing:
            del export, serve
        predict.tf.keras.backend.clear_session()
        gc.collect()
    report['status'] = 'parity-passed' if all(row['parity_passed'] for row in report['models']) else 'parity-not-confirmed'
    (args.output_dir / 'comparison.local.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path)
    parser.add_argument('--output-dir', type=Path, default=ROOT.parent / '.local-tools/lite-model-experiment')
    parser.add_argument('--model', action='append', choices=['mobilenetv2', 'efficientnetb0', 'resnet50'])
    parser.add_argument('--compare', action='store_true', help='Compare all available test images; export aggregate metrics only.')
    parser.add_argument('--verify-existing', type=Path, help='Verify the hash-pinned copies in this experiment folder without reconversion; use a separate output directory.')
    parser.add_argument('--resnet-cpu-kernel', choices=['default-delegate', 'builtin'], default='default-delegate')
    args = parser.parse_args()
    try:
        result = experiment(args)
        print(json.dumps(result), flush=True)
        sys.exit(0 if result['status'] == 'parity-passed' else 1)
    except Exception as failure:
        # Stack locations diagnose export failures without printing sample data,
        # tensor contents or arbitrary exception values.
        frames = [{'file': Path(frame.filename).name, 'line': frame.lineno, 'function': frame.name}
                  for frame in traceback.extract_tb(failure.__traceback__)]
        print(json.dumps({'status': 'experiment-not-confirmed', 'error_type': type(failure).__name__,
                          'stack': frames}), flush=True)
        sys.exit(1)
