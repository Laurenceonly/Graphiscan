"""Create and check local Lite copies of selected models; no deployment or uploads."""
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
from io import StringIO
import json
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
import train_binary_experiment as base

tf = base.tf


def run(name):
    sources = {'EfficientNetB0': 'finetune-EfficientNetB0-20261110T010325Z/EfficientNetB0_finetuned.keras',
               'ResNet50': 'finetune-ResNet50-20261110T011424Z/ResNet50_finetuned.keras'}
    original = base.OUT_ROOT / sources[name]
    expected = json.loads((original.parent / 'results.json').read_text())['artifact_sha256']
    if hashlib.sha256(original.read_bytes()).hexdigest() != expected:
        raise ValueError('Selected source does not match the recorded artifact')
    output = base.OUT_ROOT / ('lite-' + name + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(parents=True, exist_ok=False)
    print('Output:', output, flush=True)
    model = tf.keras.models.load_model(original, compile=False, safe_mode=False,
        custom_objects={'preprocess_input': tf.keras.applications.resnet50.preprocess_input})
    if tuple(model.input_shape) != (None, 224, 224, 3) or tuple(model.output_shape) != (None, 1):
        raise ValueError('Unexpected model input or output')
    print('Converting', name, 'to an isolated FP32 Lite copy.', flush=True)
    with tempfile.TemporaryDirectory(prefix='export-', dir=output) as folder, redirect_stdout(StringIO()):
        export = tf.Module()
        export.weights = [variable.value for variable in model.variables]
        @tf.function(input_signature=[tf.TensorSpec((1, 224, 224, 3), tf.float32, name='pixels')])
        def serve(pixels):
            return {'probability': model(pixels, training=False)}
        tf.saved_model.save(export, folder, signatures={'serving_default': serve})
        converter = tf.lite.TFLiteConverter.from_saved_model(folder)
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
        converter.optimizations = []
        artifact = output / (name + '_fp32.tflite')
        artifact.write_bytes(converter.convert())
    print('Comparing Keras and Lite predictions on the previously used test set.', flush=True)
    interpreter = tf.lite.Interpreter(model_path=str(artifact), num_threads=1,
        experimental_op_resolver_type=tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES)
    interpreter.allocate_tensors()
    input_id, output_id = interpreter.get_input_details()[0]['index'], interpreter.get_output_details()[0]['index']
    scores, labels, hashes, errors, disagreements = 0, [], [], [], 0
    for actual, label in enumerate(base.CLASSES):
        for path in sorted((base.DATA / 'test' / label).iterdir()):
            if path.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
                continue
            hashes.append((actual, hashlib.sha256(path.read_bytes()).hexdigest()))
            with Image.open(path) as source:
                pixels = np.asarray(ImageOps.exif_transpose(source).convert('RGB').resize((224, 224)), dtype=np.float32)[None, ...]
            ref = float(model(pixels, training=False).numpy().reshape(-1)[0])
            interpreter.set_tensor(input_id, pixels); interpreter.invoke()
            lite = float(interpreter.get_tensor(output_id).reshape(-1)[0])
            if not np.isfinite(ref) or not np.isfinite(lite):
                raise ValueError('Nonfinite model output')
            errors.append(abs(ref - lite)); disagreements += int((ref >= .75) != (lite >= .75)); scores += 1
            labels.append(actual)
            if scores % 25 == 0:
                print('Checked', scores, 'of 136 images.', flush=True)
    digest = hashlib.sha256()
    for label, image_hash in sorted(hashes):
        digest.update(f'{label}:{image_hash}\n'.encode())
    report = {'model': name, 'source_sha256': expected, 'lite_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
              'sample_count': scores, 'dataset_sha256': digest.hexdigest(), 'threshold': .75,
              'max_absolute_score_error': max(errors, default=float('inf')), 'classification_disagreements': disagreements,
              'platform': 'Windows CPU, builtin interpreter', 'test_set_previously_used': True,
              'note': 'Local conversion parity only; Linux/hosted parity, memory and independent validation remain unverified.'}
    report['parity_passed'] = scores == 136 and digest.hexdigest() == '29c3bb42a09a733eacc43489dcb9214d2b526aa1866e61114a93db943b744549' and disagreements == 0 and report['max_absolute_score_error'] <= .0001
    (output / 'parity.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)
    if not report['parity_passed']:
        raise SystemExit('Parity not confirmed; do not deploy.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('model', choices=['EfficientNetB0', 'ResNet50'])
    run(parser.parse_args().model)
