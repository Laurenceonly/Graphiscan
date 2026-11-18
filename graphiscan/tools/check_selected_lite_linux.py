"""Verify local selected FP32 Lite copies on Linux; no network or student records."""
import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '2')
os.environ.setdefault('TF_NUM_INTEROP_THREADS', '1')
import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf
from ai_edge_litert.compiled_model import CompiledModel, CpuKernelMode, CpuOptions, HardwareAccelerator, Options

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / '.local-tools/training-experiments'
SOURCES = {
    'EfficientNetB0': ('finetune-EfficientNetB0-20261110T010325Z/EfficientNetB0_finetuned.keras', 'lite-EfficientNetB0-20261110T020815Z/EfficientNetB0_fp32.tflite'),
    'ResNet50': ('finetune-ResNet50-20261110T011424Z/ResNet50_finetuned.keras', 'lite-ResNet50-20261110T021045Z/ResNet50_fp32.tflite'),
}
EXPECTED = {'EfficientNetB0': [[65, 5], [24, 42]], 'ResNet50': [[68, 2], [16, 50]]}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run(name):
    original, lite = (WORK / p for p in SOURCES[name])
    recorded = json.loads((original.parent / 'results.json').read_text())
    prior = json.loads((lite.parent / 'parity.json').read_text())
    if sha(original) != recorded['artifact_sha256'] or sha(lite) != prior['lite_sha256'] or not prior['parity_passed']:
        raise ValueError('Selected artifact verification failed')
    model = tf.keras.models.load_model(original, compile=False, safe_mode=False,
             custom_objects={'preprocess_input': tf.keras.applications.resnet50.preprocess_input})
    options = Options(hardware_accelerators=HardwareAccelerator.CPU,
                      cpu_options=CpuOptions(num_threads=1, kernel_mode=CpuKernelMode.BUILTIN)) if name == 'ResNet50' else HardwareAccelerator.CPU
    compiled = CompiledModel.from_file(str(lite), options=options) if name == 'ResNet50' else CompiledModel.from_file(str(lite), options)
    inputs, outputs = compiled.create_input_buffers(0), compiled.create_output_buffers(0)
    ref_matrix, lite_matrix = [[0, 0], [0, 0]], [[0, 0], [0, 0]]
    records, errors, count, disagreement = [], [], 0, 0
    for label, classname in enumerate(['normal', 'high_potential']):
        for image_path in sorted((ROOT / 'binary_dataset/test' / classname).iterdir()):
            if image_path.suffix.lower() not in {'.png', '.jpg', '.jpeg'}:
                continue
            records.append((label, sha(image_path)))
            with Image.open(image_path) as image:
                pixels = np.asarray(ImageOps.exif_transpose(image).convert('RGB').resize((224, 224)), dtype=np.float32)[None, ...]
            ref = float(model(pixels, training=False).numpy().reshape(-1)[0])
            inputs[0].write(np.ascontiguousarray(pixels)); compiled.run_by_index(0, inputs, outputs)
            result = float(outputs[0].read(1, np.float32)[0])
            if not np.isfinite(ref) or not np.isfinite(result):
                raise ValueError('Nonfinite score')
            errors.append(abs(ref-result)); ref_class, lite_class = int(ref >= .75), int(result >= .75)
            ref_matrix[label][ref_class] += 1; lite_matrix[label][lite_class] += 1
            disagreement += int(ref_class != lite_class); count += 1
            if count % 25 == 0: print(name, 'checked', count, 'of 136', flush=True)
    digest = hashlib.sha256()
    for label, image_hash in sorted(records): digest.update(f'{label}:{image_hash}\n'.encode())
    result = {'model': name, 'platform': 'Linux', 'kernel': 'builtin' if name == 'ResNet50' else 'CPU delegate',
              'source_sha256': sha(original), 'lite_sha256': sha(lite), 'test_count': count,
              'dataset_sha256': digest.hexdigest(), 'threshold': .75, 'max_error': max(errors, default=1),
              'disagreements': disagreement, 'reference_matrix': ref_matrix, 'lite_matrix': lite_matrix,
              'independent_validation': False, 'live_state_changed': False}
    result['passed'] = count == 136 and digest.hexdigest() == '29c3bb42a09a733eacc43489dcb9214d2b526aa1866e61114a93db943b744549' and ref_matrix == lite_matrix == EXPECTED[name] and disagreement == 0 and result['max_error'] <= .0001
    (lite.parent / 'linux-parity.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    if not result['passed']: raise SystemExit('Linux parity failed; do not deploy')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('model', choices=list(SOURCES))
    run(parser.parse_args().model)
