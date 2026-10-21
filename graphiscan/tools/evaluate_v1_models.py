"""Evaluate fixed local binary artifacts on the existing test split; never trains or publishes."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v1_uploads import PREPROCESSING_KEY, file_digest, normalize_image


def metrics(matrix):
    tn, fp = matrix[0]
    fn, tp = matrix[1]
    total = tn + fp + fn + tp
    return {'confusion_matrix': matrix, 'sample_count': total,
            'accuracy': (tn + tp) / total,
            'precision': tp / (tp + fp) if tp + fp else 0,
            'recall': tp / (tp + fn) if tp + fn else 0,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0}


def evaluate(compare=False):
    import math
    import predict
    labels = ['normal', 'high_potential']
    if predict.load_class_names() != labels:
        raise ValueError('Unsupported class mapping')
    samples = []
    digest = hashlib.sha256()
    counts = {}
    for index, label in enumerate(labels):
        directory = ROOT / 'binary_dataset/test' / label
        paths = sorted(p for p in directory.iterdir()
                       if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg'})
        if not paths:
            raise ValueError('Empty test class')
        counts[label] = len(paths)
        for path in paths:
            raw = path.read_bytes()
            content_hash = hashlib.sha256(raw).hexdigest()
            samples.append((index, content_hash, raw))
    # Bind labels and contents without disclosing image names or per-image results.
    for label, content_hash, _ in sorted(samples, key=lambda row: (row[0], row[1])):
        digest.update(f'{label}:{content_hash}\n'.encode())
    artifacts = [('ResNet50', ROOT / 'model/graphiscan_model.keras')]
    if compare:
        artifacts += [(name, ROOT / 'training_results/models' / f'{name}_best.keras')
                      for name in ['EfficientNetB0', 'MobileNetV2']]
    report = {'status': 'evaluation-complete', 'preprocessing_key': PREPROCESSING_KEY,
              'runtime_source_sha256': file_digest(ROOT / 'predict.py'),
              'class_names_sha256': file_digest(ROOT / 'model/class_names.json'),
              'split': 'existing-binary-test', 'dataset_sha256': digest.hexdigest(),
              'class_counts': counts, 'matrix_order': labels, 'models': [],
              'database_changed': False, 'registry_published': False,
              'limitations': ['Existing test split; independence/leakage not established.',
                              'Hosted normalized PNG and PIL resize path; historical training used TensorFlow resize.',
                              'No raw images or per-image predictions exported.']}
    with TemporaryDirectory(prefix='graphiscan-evaluation-') as directory:
        normalized = []
        for position, (label, _, raw) in enumerate(samples):
            target = Path(directory) / f'{position}.png'
            target.write_bytes(normalize_image(BytesIO(raw)))
            normalized.append((label, target))
        for name, artifact in artifacts:
            predict._loaded_model = None
            predict.MODEL_PATH = str(artifact)
            network = predict.load_graphiscan_model()
            matrices = {threshold: [[0, 0], [0, 0]] for threshold in (0.5, 0.75)}
            for label, path in normalized:
                raw = network.predict(predict.prepare_image(str(path)), verbose=0)
                high = float(predict.get_high_potential_probability(raw))
                if not math.isfinite(high) or not 0 <= high <= 1:
                    raise ValueError('Invalid score')
                for threshold, matrix in matrices.items():
                    matrix[label][int(high >= threshold)] += 1
            report['models'].append({'model': name, 'artifact_sha256': file_digest(artifact),
                                     'thresholds': {str(t): metrics(m) for t, m in matrices.items()}})
            print(json.dumps({'status': 'model-evaluated', 'model': name,
                              'samples': len(samples)}), flush=True)
            del network
            predict._loaded_model = None
            predict.tf.keras.backend.clear_session()
    output = ROOT / 'training_results/hosted_runtime_evaluation.local.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare', action='store_true', help='Also evaluate the two recorded binary comparison artifacts.')
    args = parser.parse_args()
    try:
        evaluate(args.compare)
    except Exception:
        print(json.dumps({'status': 'evaluation-not-confirmed', 'private_error_omitted': True}), flush=True)
        sys.exit(1)
