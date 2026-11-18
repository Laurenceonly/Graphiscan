"""Prepare a separate private model bundle from the checked selected versions."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / '.local-tools'
STAGE = WORK / 'selected-model-stage' / 'graphiscan'
BUNDLE = WORK / 'selected-model-bundle'
SELECTED = {
    'efficientnetb0': WORK / 'training-experiments/lite-EfficientNetB0-20261110T020815Z',
    'resnet50': WORK / 'training-experiments/lite-ResNet50-20261110T021045Z',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def main():
    if STAGE.exists() or BUNDLE.exists():
        raise ValueError('Existing selected staging directory; preserve it for review')
    current = json.loads((ROOT / 'model/deployment.litert.local.json').read_text())
    expected = {'efficientnetb0': [[65,5],[24,42]], 'resnet50': [[68,2],[16,50]]}
    staged = {}
    for key, folder in SELECTED.items():
        linux = json.loads((folder / 'linux-parity.json').read_text())
        win = json.loads((folder / 'parity.json').read_text())
        if (not linux.get('passed') or not win.get('parity_passed') or linux['platform'] != 'Linux'
            or linux['threshold'] != .75 or linux['test_count'] != 136 or linux['reference_matrix'] != expected[key]
            or linux['reference_matrix'] != linux['lite_matrix'] or linux['lite_sha256'] != win['lite_sha256']
            or linux['source_sha256'] != win['source_sha256']):
            raise ValueError('Model parity evidence missing or inconsistent')
        artifact = folder / (('EfficientNetB0' if key == 'efficientnetb0' else 'ResNet50') + '_fp32.tflite')
        if digest(artifact) != linux['lite_sha256']:
            raise ValueError('Selected artifact changed')
        staged[key] = (artifact, linux)
    STAGE.mkdir(parents=True)
    for file in ROOT.glob('*.py'):
        if file.name != 'config.py': shutil.copy2(file, STAGE / file.name)
    (STAGE / 'model/versions').mkdir(parents=True)
    shutil.copy2(ROOT / 'model/class_names.json', STAGE / 'model/class_names.json')
    for item in current['models']:
        key = item['model_key']
        if key in staged:
            source, evidence = staged[key]
            item['artifact_sha256'] = evidence['lite_sha256']
            item['source_artifact_sha256'] = evidence['source_sha256']
            item['model_version'] = 'binary-' + evidence['lite_sha256'][:12] + '-litert-fp32-v1'
        else:
            source = ROOT / 'model/versions' / (key + '-' + item['artifact_sha256'] + '.tflite')
        target = STAGE / 'model/versions' / (key + '-' + item['artifact_sha256'] + '.tflite')
        shutil.copyfile(source, target)
        if digest(target) != item['artifact_sha256']: raise ValueError('Staged copy differs')
    (STAGE / 'model/deployment.litert.local.json').write_text(json.dumps(current, indent=2) + '\n', encoding='utf-8')
    code = 'from pathlib import Path; from model_bundle import prepare_bundle; prepare_bundle(Path.cwd(), Path(' + repr(str(BUNDLE)) + ')); print("Candidate bundle prepared")'
    subprocess.run([sys.executable, '-c', code], cwd=STAGE, check=True)
    print(json.dumps({'status': 'candidate-bundle-prepared', 'live_changed': False, 'path': str(BUNDLE)}))


if __name__ == '__main__': main()
