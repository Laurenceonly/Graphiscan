"""Server-pinned binary model catalogue; never accepts client artifact paths."""
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

from api_v1 import BackendUnavailable
from v1_uploads import PREPROCESSING_KEY, RULE, file_digest

ROOT = Path(__file__).resolve().parent
ARCHITECTURES = {'resnet50': 'ResNet50', 'efficientnetb0': 'EfficientNetB0', 'mobilenetv2': 'MobileNetV2'}


class VersionedBinaryRuntime:
    def __init__(self, manifest_path):
        document = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
        if set(document) != {'schema_version', 'runtime_source_sha256', 'normalizer_source_sha256',
                            'adapter_source_sha256', 'class_names_sha256', 'models'} or document['schema_version'] != 2:
            raise ValueError('Invalid model catalogue')
        for field, name in [('runtime_source_sha256', 'predict.py'), ('normalizer_source_sha256', 'v1_uploads.py'),
                            ('adapter_source_sha256', 'v1_models.py'), ('class_names_sha256', 'model/class_names.json')]:
            if document[field] != file_digest(ROOT / name):
                raise ValueError('Runtime identity mismatch')
        if json.loads((ROOT / 'model/class_names.json').read_text(encoding='utf-8')) != ['normal', 'high_potential']:
            raise ValueError('Unsupported class mapping')
        if not isinstance(document['models'], list) or not 1 <= len(document['models']) <= 3:
            raise ValueError('Invalid model catalogue')
        self.entries = {}
        self.networks = {}
        self.lock = Lock()
        for entry in document['models']:
            if set(entry) != {'model_key', 'model_version', 'artifact_sha256', 'preprocessing_key', 'decision_rule'}:
                raise ValueError('Invalid model entry')
            key = entry['model_key']
            digest = entry['artifact_sha256']
            if key not in ARCHITECTURES or key in self.entries or not isinstance(entry['model_version'], str) or not entry['model_version'].strip():
                raise ValueError('Invalid model identity')
            import re
            if not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest):
                raise ValueError('Invalid artifact digest')
            if entry['preprocessing_key'] != PREPROCESSING_KEY or entry['decision_rule'] != RULE:
                raise ValueError('Unsupported preprocessing/rule')
            artifact = ROOT / 'model/versions' / f'{key}-{digest}.keras'
            if file_digest(artifact) != digest:
                raise ValueError('Artifact identity mismatch')
            self.entries[key] = (dict(entry), artifact)

    def supports(self, model):
        found = self.entries.get(model.get('model_key'))
        return bool(found and model.get('task_type') == 'binary' and model.get('provenance', 'verified') == 'verified'
                    and all(model.get(key) == found[0][key] for key in ('model_key', 'model_version', 'preprocessing_key', 'decision_rule'))
                    and ('artifact_sha256' not in model or model['artifact_sha256'] == found[0]['artifact_sha256']))

    def identity_for(self, model):
        return dict(self.entries[model['model_key']][0]) if self.supports(model) else {}

    def infer(self, data, model):
        if not self.supports(model):
            raise BackendUnavailable()
        entry, artifact = self.entries[model['model_key']]
        if model.get('artifact_sha256') != entry['artifact_sha256']:
            raise BackendUnavailable()
        import predict
        import numpy as np
        # A single lock serializes lazy model loading and inference without mutating
        # predict's legacy global model/path/class mapping or sharing them across versions.
        with self.lock:
            network = self.networks.get(entry['model_key'])
            if network is None:
                if file_digest(artifact) != entry['artifact_sha256']:
                    raise BackendUnavailable()
                network = predict.load_model(str(artifact), compile=False, safe_mode=False,
                    custom_objects={'preprocess_input': predict.resnet50_preprocess_input})
                if tuple(network.input_shape) != (None, 224, 224, 3) or tuple(network.output_shape) != (None, 1):
                    raise BackendUnavailable()
                self.networks[entry['model_key']] = network
            with TemporaryDirectory(prefix='graphiscan-model-') as folder:
                path = Path(folder) / 'sample.png'
                path.write_bytes(data)
                scores = np.asarray(network.predict(predict.prepare_image(str(path)), verbose=0))
            if scores.shape != (1, 1):
                raise BackendUnavailable()
            high = float(scores[0, 0])
        if not math.isfinite(high) or not 0 <= high <= 1:
            raise BackendUnavailable()
        label = predict.classify_result(high)['classification']
        return {'classification': label, 'class_scores': {'normal': 1-high, 'high_potential': high},
                'predicted_class_score': round(high if label == 'High Potential' else 1-high, 5)}


def runtime_from_manifest(path):
    document = json.loads(Path(path).read_text(encoding='utf-8'))
    if document.get('schema_version') == 2:
        return VersionedBinaryRuntime(path)
    from v1_uploads import ActiveBinaryRuntime
    return ActiveBinaryRuntime(path)
