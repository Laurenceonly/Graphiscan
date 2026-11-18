"""Verify the selected private bundle and prepare a separate, reversible cutover."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / '.local-tools'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    bundle = WORK / 'selected-model-bundle'
    descriptor = json.loads((bundle / 'descriptor.json').read_text())
    for item in descriptor['files']:
        content = b''
        for part in item['parts']:
            path = bundle / 'parts' / part['sha256']
            if path.stat().st_size != part['size'] or sha(path) != part['sha256']:
                raise ValueError('Private chunk identity mismatch')
            content += path.read_bytes()
        if len(content) != item['size'] or hashlib.sha256(content).hexdigest() != item['sha256']:
            raise ValueError('Bundle identity mismatch')
    manifest = json.loads((WORK / 'selected-model-stage/graphiscan/model/deployment.litert.local.json').read_text())
    for field, name in [('runtime_source_sha256', 'predict.py'), ('normalizer_source_sha256', 'v1_uploads.py'),
                        ('legacy_adapter_source_sha256', 'v1_models.py'), ('adapter_source_sha256', 'v1_lite_models.py'),
                        ('class_names_sha256', 'model/class_names.json')]:
        if manifest[field] != sha(ROOT / name):
            raise ValueError('Runtime source identity mismatch')
    manifest_item = next(i for i in descriptor['files'] if i['path'] == 'model/deployment.litert.local.json')
    if manifest_item['sha256'] != sha(WORK / 'selected-model-stage/graphiscan/model/deployment.litert.local.json'):
        raise ValueError('Manifest identity mismatch')
    old_sql = (ROOT / 'db/postgres/publish_lite_binary_models.sql').read_text()
    old_specs = json.loads(re.search(r"DECLARE config jsonb := '(.*?)'::jsonb", old_sql)[1])
    specs, evidence = [], []
    for key, name, folder, matrix in [
        ('efficientnetb0', 'EfficientNetB0', 'lite-EfficientNetB0-20261110T020815Z', [[65,5],[24,42]]),
        ('resnet50', 'ResNet50', 'lite-ResNet50-20261110T021045Z', [[68,2],[16,50]])]:
        row = json.loads((WORK / 'training-experiments' / folder / 'linux-parity.json').read_text())
        entry = next(i for i in manifest['models'] if i['model_key'] == key)
        if (row['passed'] is not True or row['platform'] != 'Linux' or row['test_count'] != 136
                or row['threshold'] != .75 or row['reference_matrix'] != matrix or row['lite_matrix'] != matrix
                or row['disagreements'] != 0 or row['max_error'] > .0001
                or entry['artifact_sha256'] != row['lite_sha256'] or entry['source_artifact_sha256'] != row['source_sha256']
                or not any(i['sha256'] == row['lite_sha256'] for i in descriptor['files'])):
            raise ValueError('Selected parity evidence mismatch')
        old = next(i for i in old_specs if i['model_key'] == key)
        specs.append(dict(model_key=key, architecture=name, previous_version=old['model_version'],
                          previous_accuracy=old['test_accuracy'], model_version=entry['model_version'],
                          test_accuracy=round((matrix[0][0]+matrix[1][1])/136, 5)))
        evidence.append(row)
    mobile = next(i for i in manifest['models'] if i['model_key'] == 'mobilenetv2')
    if mobile['model_version'] != next(i for i in old_specs if i['model_key'] == 'mobilenetv2')['model_version']:
        raise ValueError('MobileNet must remain unchanged')
    report = ROOT / 'api/selected-litert-evaluation.json'
    report.write_text(json.dumps({'models': evidence, 'independent_validation': False}, indent=2)+'\n')
    sql = re.sub(r"DECLARE config jsonb := '.*?'::jsonb", "DECLARE config jsonb := '"+json.dumps(specs,separators=(',', ':'))+"'::jsonb", old_sql)
    sql = sql.replace('api/litert-linux-evaluation.json', 'api/selected-litert-evaluation.json')
    sql = sql.replace("'binary-ecad77ab7de3-hosted-v1','binary-3abdc7ee4b2b-litert-fp32-v1'", "'binary-3abdc7ee4b2b-litert-fp32-v1'")
    # Old-version guards use the old evaluation and accuracy. New rows use selected evidence.
    prefix, tail = sql.split('END LOOP;', 1)
    prefix = prefix.replace("spec->>'test_accuracy'", "spec->>'previous_accuracy'")
    prefix = prefix.replace('test-hosted-normalized-threshold-075', 'test-hosted-litert-fp32-builtin-resnet-threshold-075')
    old_ref = re.search(r"evidence_reference='(sha256:[a-f0-9]+)'", tail)[1]
    tail = tail.replace(old_ref, 'sha256:'+sha(report)).replace('test-hosted-litert-fp32-builtin-resnet-threshold-075', 'test-selected-litert-fp32-threshold-075')
    sql = prefix+'END LOOP;'+tail
    rollback = prefix+'END LOOP;'+sql[sql.index('UPDATE public.model_registry m SET'):]
    rollback = rollback.replace("s->>'previous_version'", "s->>'TEMP'").replace("s->>'model_version'", "s->>'previous_version'").replace("s->>'TEMP'", "s->>'model_version'")
    rollback = rollback.replace('-- Optional model-data cutover', '-- Optional model-data rollback')
    for name, text in [('publish_selected_binary_models.sql', sql), ('rollback_selected_binary_models.sql', rollback)]:
        (ROOT / 'db/postgres' / name).write_text(text)
    # Kept separate until private upload and cutover tests pass.
    (ROOT / 'model/selected-litert-bundle.json').write_text(json.dumps(descriptor, indent=2)+'\n')
    print(json.dumps({'status': 'selected-publication-prepared', 'models_replaced': 2, 'database_changed': False}))


if __name__ == '__main__':
    main()
