"""Opt-in LiteRT FP32 catalogue; preserves the existing Keras runtime unchanged."""
from io import BytesIO
import json
import math
from pathlib import Path
import re
from threading import Lock

from api_v1 import BackendUnavailable
from v1_models import ARCHITECTURES, ROOT, VersionedBinaryRuntime
from v1_uploads import PREPROCESSING_KEY, RULE, file_digest

RUNTIME_KIND = 'litert-fp32-builtin-resnet-v1'
RESNET_CPU_KERNEL = 'builtin'


def _digest(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


class LiteBinaryRuntime(VersionedBinaryRuntime):
    """Same upload-service contract, distinct artifacts/versions, one cached model.

    Subclassing retains the upload service's versioned-catalogue identity checks.
    Neither loading this module nor constructing it imports TensorFlow.
    """

    def __init__(self, manifest_path):
        document = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
        fields = {'schema_version', 'runtime_kind', 'runtime_source_sha256',
                  'normalizer_source_sha256', 'legacy_adapter_source_sha256',
                  'adapter_source_sha256', 'class_names_sha256', 'models'}
        if set(document) != fields or document['schema_version'] != 3 or document['runtime_kind'] != RUNTIME_KIND:
            raise ValueError('Invalid lightweight catalogue')
        sources = [('runtime_source_sha256', 'predict.py'),
                   ('normalizer_source_sha256', 'v1_uploads.py'),
                   ('legacy_adapter_source_sha256', 'v1_models.py'),
                   ('adapter_source_sha256', 'v1_lite_models.py'),
                   ('class_names_sha256', 'model/class_names.json')]
        if any(document[field] != file_digest(ROOT / name) for field, name in sources):
            raise ValueError('Lightweight runtime identity mismatch')
        if json.loads((ROOT / 'model/class_names.json').read_text(encoding='utf-8')) != ['normal', 'high_potential']:
            raise ValueError('Unsupported class mapping')
        if not isinstance(document['models'], list) or not 1 <= len(document['models']) <= 3:
            raise ValueError('Invalid lightweight models')
        self.entries, self.networks, self.lock = {}, {}, Lock()
        for item in document['models']:
            if set(item) != {'model_key', 'model_version', 'artifact_sha256', 'source_artifact_sha256',
                             'preprocessing_key', 'decision_rule'}:
                raise ValueError('Invalid lightweight identity')
            key, digest = item['model_key'], item['artifact_sha256']
            if key not in ARCHITECTURES or key in self.entries or not _digest(digest) or not _digest(item['source_artifact_sha256']):
                raise ValueError('Invalid lightweight artifact')
            if item['model_version'] != f'binary-{digest[:12]}-litert-fp32-v1':
                raise ValueError('Lightweight artifact requires a distinct version')
            if item['preprocessing_key'] != PREPROCESSING_KEY or item['decision_rule'] != RULE:
                raise ValueError('Unsupported preprocessing/rule')
            artifact = ROOT / 'model/versions' / f'{key}-{digest}.tflite'
            if file_digest(artifact) != digest:
                raise ValueError('Lightweight artifact identity mismatch')
            # SQL receives the same five-field identity as the Keras catalogue.
            entry = {name: value for name, value in item.items() if name != 'source_artifact_sha256'}
            self.entries[key] = (entry, artifact)

    def _load(self, key, artifact, digest):
        if file_digest(artifact) != digest:
            raise BackendUnavailable()
        import numpy as np
        from ai_edge_litert.compiled_model import CompiledModel, CpuKernelMode, CpuOptions, HardwareAccelerator, Options
        # Release the previous model before compiling another architecture.
        # The lock in infer also protects buffers and cache eviction.
        for cached, _, _ in self.networks.values():
            cached.close()
        self.networks.clear()
        if key == 'resnet50':
            # Verified on the full Linux split. Builtin kernels avoid the large
            # delegate weight pack retained by this architecture on a small host.
            network = CompiledModel.from_file(str(artifact), options=Options(
                hardware_accelerators=HardwareAccelerator.CPU,
                cpu_options=CpuOptions(num_threads=1, kernel_mode=CpuKernelMode.BUILTIN)))
        else:
            network = CompiledModel.from_file(str(artifact), HardwareAccelerator.CPU)
        try:
            inputs = list(network.get_input_tensor_details('serving_default').values())
            outputs = list(network.get_output_tensor_details('serving_default').values())
            if (network.get_num_signatures() != 1 or network.get_signature_index('serving_default') != 0
                    or len(inputs) != 1 or len(outputs) != 1
                    or tuple(inputs[0]['shape']) != (1, 224, 224, 3)
                    or tuple(outputs[0]['shape']) != (1, 1)
                    or np.dtype(inputs[0]['dtype']) != np.dtype('float32')
                    or np.dtype(outputs[0]['dtype']) != np.dtype('float32')):
                raise BackendUnavailable()
            buffers = (network, network.create_input_buffers(0), network.create_output_buffers(0))
            if len(buffers[1]) != 1 or len(buffers[2]) != 1:
                raise BackendUnavailable()
        except Exception:
            network.close()
            raise
        self.networks[key] = buffers
        return buffers

    def infer(self, data, model):
        if not self.supports(model):
            raise BackendUnavailable()
        entry, artifact = self.entries[model['model_key']]
        if model.get('artifact_sha256') != entry['artifact_sha256']:
            raise BackendUnavailable()
        import numpy as np
        from PIL import Image

        with self.lock:
            network, inputs, outputs = self.networks.get(entry['model_key']) or self._load(
                entry['model_key'], artifact, entry['artifact_sha256'])
            # data is the upload service's EXIF-normalized PNG. Match
            # predict.prepare_image exactly: RGB, PIL default resize, raw FP32.
            with Image.open(BytesIO(data)) as image:
                pixels = np.array(image.convert('RGB').resize((224, 224))).astype('float32')[None]
            inputs[0].write(pixels)
            network.run_by_index(0, inputs, outputs)
            scores = np.asarray(outputs[0].read(1, np.float32))
            if scores.shape != (1,):
                raise BackendUnavailable()
            high = float(scores[0])
        if not math.isfinite(high) or not 0 <= high <= 1:
            raise BackendUnavailable()
        label = 'High Potential' if high >= RULE['threshold'] else 'Normal'
        return {'classification': label, 'class_scores': {'normal': 1-high, 'high_potential': high},
                'predicted_class_score': round(high if label == 'High Potential' else 1-high, 5)}


def runtime_from_manifest(path):
    document = json.loads(Path(path).read_text(encoding='utf-8'))
    if document.get('schema_version') == 3:
        return LiteBinaryRuntime(path)
    from v1_models import runtime_from_manifest as legacy_runtime
    return legacy_runtime(path)
