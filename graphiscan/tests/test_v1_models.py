import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from api_v1 import BackendUnavailable
from v1_models import VersionedBinaryRuntime
from v1_uploads import PREPROCESSING_KEY,RULE


class VersionedModelTests(unittest.TestCase):
    def runtime(self):
        entries=[{'model_key':key,'model_version':'test-v1','artifact_sha256':letter*64,
                  'preprocessing_key':PREPROCESSING_KEY,'decision_rule':RULE}
                 for key,letter in [('resnet50','a'),('mobilenetv2','b')]]
        document={'schema_version':2,'runtime_source_sha256':'c'*64,'normalizer_source_sha256':'c'*64,
                  'adapter_source_sha256':'c'*64,'class_names_sha256':'c'*64,'models':entries}
        def digest(path):
            return 'a'*64 if path.name.startswith('resnet50-') else 'b'*64 if path.name.startswith('mobilenetv2-') else 'c'*64
        with TemporaryDirectory() as folder:
            target=Path(folder)/'catalogue.json';target.write_text(json.dumps(document),encoding='utf-8')
            original=Path.read_text
            def read(path,*args,**kwargs):
                return '["normal","high_potential"]' if path.name=='class_names.json' else original(path,*args,**kwargs)
            with patch('v1_models.file_digest',side_effect=digest),patch.object(Path,'read_text',read):
                runtime=VersionedBinaryRuntime(target)
        return runtime,entries,digest

    def test_identity_is_bound_to_version_rule_and_artifact(self):
        runtime,entries,_=self.runtime()
        model={**entries[1],'task_type':'binary'}
        self.assertTrue(runtime.supports(model))
        for changed in [{'model_version':'other'},{'decision_rule':{'kind':'high_potential_threshold','threshold':0.5}},
                        {'artifact_sha256':'a'*64},{'task_type':'three_class'},{'provenance':'legacy_unverified'}]:
            self.assertFalse(runtime.supports({**model,**changed}))
        self.assertEqual(runtime.identity_for(model),entries[1])
        self.assertEqual(runtime.identity_for({'model_key':'../secret'}),{})

    def test_versions_have_distinct_cached_networks_and_no_legacy_mutation(self):
        runtime,entries,digest=self.runtime()
        first=Mock(input_shape=(None,224,224,3),output_shape=(None,1))
        second=Mock(input_shape=(None,224,224,3),output_shape=(None,1))
        first.predict.return_value=[[0.6]];second.predict.return_value=[[0.8]]
        predictor=SimpleNamespace(load_model=Mock(side_effect=[first,second]),resnet50_preprocess_input=object(),
            prepare_image=lambda path:None,classify_result=lambda high:{'classification':'High Potential' if high>=0.75 else 'Normal'},
            MODEL_PATH='legacy-unchanged',_loaded_model='legacy-network')
        with patch('v1_models.file_digest',side_effect=digest),patch.dict('sys.modules',{'predict':predictor}):
            normal=runtime.infer(b'fictional',{**entries[0],'task_type':'binary'})
            high=runtime.infer(b'fictional',{**entries[1],'task_type':'binary'})
            runtime.infer(b'fictional',{**entries[0],'task_type':'binary'})
            self.assertEqual(normal['classification'],'Normal')
            self.assertEqual(normal['predicted_class_score'],0.4)
            self.assertEqual(high['classification'],'High Potential')
            self.assertEqual(predictor.load_model.call_count,2)
            self.assertEqual(predictor.MODEL_PATH,'legacy-unchanged')
            self.assertEqual(predictor._loaded_model,'legacy-network')
            second.predict.return_value=[[float('nan')]]
            with self.assertRaises(BackendUnavailable):runtime.infer(b'x',{**entries[1],'task_type':'binary'})

    def test_artifact_changed_before_lazy_load_is_denied(self):
        runtime,entries,_=self.runtime()
        with patch.dict('sys.modules',{'predict':SimpleNamespace()}),patch('v1_models.file_digest',return_value='f'*64):
            with self.assertRaises(BackendUnavailable):runtime.infer(b'x',{**entries[0],'task_type':'binary'})


if __name__=='__main__':unittest.main()
