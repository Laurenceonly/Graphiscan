"""Measure selected Keras models on the existing, previously used test set."""
from datetime import datetime, timezone
import hashlib
import json
import train_binary_experiment as base

tf = base.tf


def main():
    root = base.OUT_ROOT
    sources = {
        'MobileNetV2': base.ROOT / 'training_results/models/MobileNetV2_best.keras',
        'EfficientNetB0': root / 'finetune-EfficientNetB0-20261110T010325Z/EfficientNetB0_finetuned.keras',
        'ResNet50': root / 'finetune-ResNet50-20261110T011424Z/ResNet50_finetuned.keras',
    }
    recorded = {
        'EfficientNetB0': root / 'finetune-EfficientNetB0-20261110T010325Z/results.json',
        'ResNet50': root / 'finetune-ResNet50-20261110T011424Z/results.json',
    }
    output = root / ('selected-test-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(parents=True, exist_ok=False)
    print('Output:', output, flush=True)
    results = {'threshold': .75, 'split': 'previously used test set',
               'limitation': 'Not independent; prior comparisons used these images and writer separation is unverified.', 'models': {}}
    for name, path in sources.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if name in recorded and digest != json.loads(recorded[name].read_text())['artifact_sha256']:
            raise ValueError('Selected artifact hash mismatch')
        print('Evaluating', name, flush=True)
        model = tf.keras.models.load_model(path, compile=False, safe_mode=False,
                custom_objects={'preprocess_input': tf.keras.applications.resnet50.preprocess_input})
        measured = base.evaluate(model, split='test')
        if measured['n'] != 136 or measured['dataset_sha256'] != '29c3bb42a09a733eacc43489dcb9214d2b526aa1866e61114a93db943b744549':
            raise ValueError('Unexpected test dataset')
        results['models'][name] = {'artifact_sha256': digest, 'evaluation': measured}
        (output / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        base.confusion_graph(name, measured['confusion_matrix'], output)
        base.comparison_graphs(results, output)
        print(name, json.dumps(measured), flush=True)
        del model
        tf.keras.backend.clear_session()
    print('Complete. No model or catalogue was deployed.', flush=True)


if __name__ == '__main__':
    main()
