"""Stage parity-checked FP32 copies locally; no environment or database changes."""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v1_lite_models import LiteBinaryRuntime, RESNET_CPU_KERNEL, RUNTIME_KIND
from v1_models import ARCHITECTURES, VersionedBinaryRuntime
from v1_uploads import PREPROCESSING_KEY, RULE, file_digest


def prepare(comparison, artifact_dir=None, refresh_draft=False):
    report = json.loads(comparison.read_text(encoding='utf-8'))
    evidence = json.loads((ROOT / 'training_results/hosted_runtime_evaluation.local.json').read_text(encoding='utf-8'))
    original = VersionedBinaryRuntime(ROOT / 'model/deployment.local.json')
    if (report.get('status') != 'parity-passed' or report.get('quantization') != 'none-float32'
            or report.get('split') != 'existing-binary-test' or report.get('sample_count') != 136
            or report.get('decision_threshold') != .75 or report.get('score_tolerance') != .0001
            or report.get('platform') != 'Linux' or report.get('resnet_cpu_kernel') != RESNET_CPU_KERNEL
            or evidence.get('status') != 'evaluation-complete'
            or report.get('dataset_sha256') != evidence['dataset_sha256']
            or evidence.get('class_counts') != {'normal': 70, 'high_potential': 66}):
        raise ValueError('Require the verified original split and completed FP32 comparison')
    rows = report.get('models', [])
    if len(rows) != 3 or {row['model_key'] for row in rows} != set(ARCHITECTURES):
        raise ValueError('Require all three architectures')
    document = {'schema_version': 3, 'runtime_kind': RUNTIME_KIND, 'models': []}
    for field, name in [('runtime_source_sha256', 'predict.py'),
                        ('normalizer_source_sha256', 'v1_uploads.py'),
                        ('legacy_adapter_source_sha256', 'v1_models.py'),
                        ('adapter_source_sha256', 'v1_lite_models.py'),
                        ('class_names_sha256', 'model/class_names.json')]:
        document[field] = file_digest(ROOT / name)
    copies = []
    for row in rows:
        key, digest = row['model_key'], row['converted_artifact_sha256']
        source_entry, _ = original.entries[key]
        measured = next(item for item in evidence['models'] if item['model'] == ARCHITECTURES[key])
        expected_matrix = measured['thresholds']['0.75']['confusion_matrix']
        error = row.get('max_absolute_score_error')
        if (row.get('parity_passed') is not True or row.get('classification_disagreements') != 0
                or type(error) not in (int, float) or not math.isfinite(error) or not 0 <= error <= .0001
                or row.get('source_artifact_sha256') != source_entry['artifact_sha256']
                or measured['artifact_sha256'] != source_entry['artifact_sha256']
                or row.get('reference_confusion_matrix') != expected_matrix
                or row.get('converted_confusion_matrix') != expected_matrix):
            raise ValueError('Unverified lightweight model')
        import re
        if not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None:
            raise ValueError('Invalid converted identity')
        source = (artifact_dir or comparison.parent) / f'{key}-{source_entry["artifact_sha256"]}-fp32.tflite'
        if file_digest(source) != digest:
            raise ValueError('Changed converted artifact')
        target = ROOT / 'model/versions' / f'{key}-{digest}.tflite'
        copies.append((source, target, digest))
        document['models'].append({'model_key': key, 'model_version': f'binary-{digest[:12]}-litert-fp32-v1',
            'artifact_sha256': digest, 'source_artifact_sha256': source_entry['artifact_sha256'],
            'preprocessing_key': PREPROCESSING_KEY, 'decision_rule': RULE})
    destination = ROOT / 'model/deployment.litert.local.json'
    serialized = json.dumps(document, indent=2) + '\n'
    if destination.exists() and destination.read_text(encoding='utf-8') != serialized:
        previous = json.loads(destination.read_text(encoding='utf-8'))
        current = dict(document)
        for name in ('runtime_kind', 'adapter_source_sha256'):
            previous.pop(name, None)
            current.pop(name, None)
        if not refresh_draft or previous != current:
            raise ValueError('Existing draft catalogue differs; review it before replacement')
        previous_digest = file_digest(destination)
        backup = destination.with_name(f'deployment.litert-{previous_digest}.local.json')
        if backup.exists() and file_digest(backup) != previous_digest:
            raise ValueError('Existing private draft backup differs')
        if not backup.exists():
            shutil.copyfile(destination, backup)
    for source, target, digest in copies:
        if not target.exists():
            shutil.copyfile(source, target)
        if file_digest(target) != digest:
            raise ValueError('Staged lightweight artifact mismatch')
    destination.write_text(serialized, encoding='utf-8')
    runtime = LiteBinaryRuntime(destination)
    return {'status': 'lightweight-catalogue-staged', 'models': len(runtime.entries),
            'manifest': 'model/deployment.litert.local.json', 'comparison_sha256': file_digest(comparison),
            'environment_changed': False, 'registry_published': False, 'database_accessed': False,
            'live_deployment_changed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison', type=Path, default=ROOT.parent / '.local-tools/lite-model-experiment/comparison.local.json')
    parser.add_argument('--artifact-dir', type=Path, help='Existing converted files when the Linux report is in a separate folder.')
    parser.add_argument('--refresh-draft', action='store_true', help='Back up and refresh only runtime-kind/adapter pins in the separate unpublished draft; artifact identities cannot change.')
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.comparison, args.artifact_dir, args.refresh_draft)), flush=True)
    except Exception as failure:
        print(json.dumps({'status': 'lightweight-catalogue-not-staged', 'error_type': type(failure).__name__}), flush=True)
        sys.exit(1)
