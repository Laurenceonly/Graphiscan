"""Lightweight runtime identity, cache and preprocessing boundary checks."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api_v1 import BackendUnavailable
import v1_lite_models as lite
from v1_models import VersionedBinaryRuntime
from v1_uploads import PREPROCESSING_KEY, RULE, file_digest


class LiteModelTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / 'model/versions').mkdir(parents=True)
        self.patcher = patch.object(lite, 'ROOT', self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        sources = [('runtime_source_sha256', 'predict.py'), ('normalizer_source_sha256', 'v1_uploads.py'),
                   ('legacy_adapter_source_sha256', 'v1_models.py'), ('adapter_source_sha256', 'v1_lite_models.py'),
                   ('class_names_sha256', 'model/class_names.json')]
        self.document = {'schema_version': 3, 'runtime_kind': lite.RUNTIME_KIND, 'models': []}
        for field, name in sources:
            path = self.root / name
            path.write_text('["normal", "high_potential"]' if name.endswith('.json') else 'fictional source', encoding='utf-8')
            self.document[field] = file_digest(path)
        for key in ('mobilenetv2', 'resnet50'):
            content = ('fictional ' + key).encode()
            digest = hashlib.sha256(content).hexdigest()
            (self.root / 'model/versions' / f'{key}-{digest}.tflite').write_bytes(content)
            self.document['models'].append({'model_key': key, 'model_version': f'binary-{digest[:12]}-litert-fp32-v1',
                'artifact_sha256': digest, 'source_artifact_sha256': 'a'*64,
                'preprocessing_key': PREPROCESSING_KEY, 'decision_rule': RULE})
        self.manifest = self.root / 'manifest.json'
        self.save()
        self.runtime = lite.LiteBinaryRuntime(self.manifest)
        stream = BytesIO()
        Image.new('RGB', (300, 200), (255, 128, 0)).save(stream, format='PNG')
        self.image = stream.getvalue()

    def save(self):
        self.manifest.write_text(json.dumps(self.document), encoding='utf-8')

    def model(self, index=0):
        entry = self.document['models'][index]
        return {name: value for name, value in entry.items() if name != 'source_artifact_sha256'} | {'task_type': 'binary'}

    def network(self, score=.8):
        network = Mock()
        network.get_num_signatures.return_value = 1
        network.get_signature_index.return_value = 0
        network.get_input_tensor_details.return_value = {'pixels': {'shape': (1, 224, 224, 3), 'dtype': np.float32}}
        network.get_output_tensor_details.return_value = {'probability': {'shape': (1, 1), 'dtype': np.float32}}
        inputs, outputs = Mock(), Mock()
        outputs.read.return_value = np.array([score], dtype=np.float32)
        network.create_input_buffers.return_value = [inputs]
        network.create_output_buffers.return_value = [outputs]
        return network, inputs, outputs

    def library(self, *networks):
        factory = Mock(side_effect=networks)
        module = SimpleNamespace(CompiledModel=SimpleNamespace(from_file=factory),
                                 HardwareAccelerator=SimpleNamespace(CPU='cpu'),
                                 CpuKernelMode=SimpleNamespace(BUILTIN='builtin'),
                                 CpuOptions=lambda **options: SimpleNamespace(**options),
                                 Options=lambda **options: SimpleNamespace(**options))
        return patch.dict(sys.modules, {'ai_edge_litert.compiled_model': module}), factory

    def test_distinct_identity_and_existing_upload_contract(self):
        self.assertIsInstance(self.runtime, VersionedBinaryRuntime)
        model = self.model()
        self.assertTrue(self.runtime.supports(model))
        self.assertNotIn('source_artifact_sha256', self.runtime.identity_for(model))
        for change in ({'model_version': 'original-keras-version'}, {'task_type': 'three_class'},
                       {'artifact_sha256': 'f'*64}, {'provenance': 'legacy_unverified'}):
            self.assertFalse(self.runtime.supports(model | change))
            with self.assertRaises(BackendUnavailable):
                self.runtime.infer(self.image, model | change)

    def test_exact_raw_rgb_preprocessing_and_threshold(self):
        network, inputs, outputs = self.network(.75)
        library, _ = self.library(network)
        with library:
            result = self.runtime.infer(self.image, self.model())
            pixels = inputs.write.call_args.args[0]
            self.assertEqual(pixels.shape, (1, 224, 224, 3))
            self.assertEqual(pixels.dtype, np.float32)
            np.testing.assert_array_equal(pixels[0, 0, 0], [255, 128, 0])
            self.assertEqual(result['classification'], 'High Potential')
            self.assertEqual(result['predicted_class_score'], .75)
            outputs.read.return_value = np.array([.5], dtype=np.float32)
            self.assertEqual(self.runtime.infer(self.image, self.model())['classification'], 'Normal')

    def test_switching_models_closes_previous_cache(self):
        first, second, third = self.network()[0], self.network()[0], self.network()[0]
        library, factory = self.library(first, second, third)
        with library:
            self.runtime.infer(self.image, self.model())
            self.runtime.infer(self.image, self.model())
            self.runtime.infer(self.image, self.model(1))
            first.close.assert_called_once()
            self.assertEqual(list(self.runtime.networks), ['resnet50'])
            self.runtime.infer(self.image, self.model())
            second.close.assert_called_once()
            self.assertEqual(factory.call_count, 3)
            options = factory.call_args_list[1].kwargs['options']
            self.assertEqual(options.cpu_options.kernel_mode, 'builtin')
            self.assertEqual(options.cpu_options.num_threads, 1)

    def test_previous_experimental_kernel_identity_is_rejected(self):
        self.document['runtime_kind'] = 'litert-fp32-v1'
        self.save()
        with self.assertRaises(ValueError):
            lite.LiteBinaryRuntime(self.manifest)

    def test_changed_artifact_or_source_is_rejected(self):
        artifact = self.runtime.entries['mobilenetv2'][1]
        artifact.write_bytes(b'changed')
        with self.assertRaises(BackendUnavailable):
            self.runtime.infer(self.image, self.model())
        (self.root / 'predict.py').write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            lite.LiteBinaryRuntime(self.manifest)

    def test_invalid_layout_and_nonfinite_scores_are_rejected(self):
        network, _, outputs = self.network()
        library, _ = self.library(network)
        with library:
            for score in (float('nan'), float('inf'), -.01, 1.01):
                outputs.read.return_value = np.array([score], dtype=np.float32)
                with self.assertRaises(BackendUnavailable):
                    self.runtime.infer(self.image, self.model())
        network, _, _ = self.network()
        network.get_input_tensor_details.return_value = {'pixels': {'shape': (1, 128, 128, 3), 'dtype': np.float32}}
        self.runtime.networks.clear()
        library, _ = self.library(network)
        with library, self.assertRaises(BackendUnavailable):
            self.runtime.infer(self.image, self.model())
        network.close.assert_called_once()

    def test_old_manifest_dispatch_stays_with_existing_factory(self):
        self.manifest.write_text('{"schema_version": 2}', encoding='utf-8')
        with patch('v1_models.runtime_from_manifest', return_value='existing-runtime') as factory:
            self.assertEqual(lite.runtime_from_manifest(self.manifest), 'existing-runtime')
            factory.assert_called_once_with(self.manifest)


if __name__ == '__main__':
    unittest.main()
