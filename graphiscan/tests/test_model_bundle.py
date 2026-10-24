"""Private model transport tests with fictional chunks and no external access."""
from copy import deepcopy
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_bundle import MANIFEST, fetch_bundle, validate_descriptor


class ModelBundleTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.document = {'schema_version': 1, 'files': []}
        self.parts, self.contents = {}, {}
        for key in ('manifest', 'mobilenetv2', 'efficientnetb0', 'resnet50'):
            content = ('fictional model ' + key).encode()
            digest = hashlib.sha256(content).hexdigest()
            path = MANIFEST if key == 'manifest' else f'model/versions/{key}-{digest}.tflite'
            self.contents[path] = content
            parts = []
            for block in (content[:6], content[6:]):
                checksum = hashlib.sha256(block).hexdigest()
                self.parts['sha256/'+checksum] = block
                parts.append({'sha256': checksum, 'size': len(block)})
            self.document['files'].append({'path': path, 'size': len(content), 'sha256': digest, 'parts': parts})
        self.client = Mock()
        self.client.get_object.side_effect = lambda **request: {
            'ContentLength': len(self.parts[request['Key']]), 'Body': BytesIO(self.parts[request['Key']])}

    def test_verified_files_are_installed_with_manifest_last_and_reused(self):
        replace = os.replace
        with patch('model_bundle.os.replace', wraps=replace) as installation:
            manifest = fetch_bundle(self.document, self.client, 'fixture-models', self.root)
        self.assertEqual(manifest, self.root / MANIFEST)
        self.assertEqual(installation.call_args_list[-1].args[1], manifest)
        for name, content in self.contents.items():
            self.assertEqual((self.root / name).read_bytes(), content)
        self.client.reset_mock()
        fetch_bundle(self.document, self.client, 'fixture-models', self.root)
        self.client.get_object.assert_not_called()

    def test_path_escape_duplicate_architecture_and_oversized_chunk_are_rejected_before_fetch(self):
        cases = []
        escaped = deepcopy(self.document)
        escaped['files'][0]['path'] = '../.env'
        cases.append(escaped)
        duplicated = deepcopy(self.document)
        duplicated['files'][2] = duplicated['files'][1]
        cases.append(duplicated)
        oversized = deepcopy(self.document)
        oversized['files'][1]['parts'][0]['size'] = 33*1024*1024
        cases.append(oversized)
        for document in cases:
            with self.assertRaises(ValueError):
                fetch_bundle(document, self.client, 'fixture-models', self.root)
        self.client.get_object.assert_not_called()

    def test_corrupt_chunk_changes_no_destination_and_closes_stream(self):
        old = self.root / MANIFEST
        old.parent.mkdir()
        old.write_bytes(b'previous manifest')
        stream = BytesIO(b'x'*6)
        self.client.get_object.side_effect = None
        self.client.get_object.return_value = {'ContentLength': 6, 'Body': stream}
        with self.assertRaises(ValueError):
            fetch_bundle(self.document, self.client, 'fixture-models', self.root)
        self.assertTrue(stream.closed)
        self.assertEqual(old.read_bytes(), b'previous manifest')
        self.assertFalse((self.root / 'model/versions').exists())

    def test_oversized_stream_is_bounded_even_if_declared_length_matches(self):
        stream = Mock()
        stream.read.return_value = b'x'*7
        self.client.get_object.side_effect = None
        self.client.get_object.return_value = {'ContentLength': 6, 'Body': stream}
        with self.assertRaises(ValueError):
            fetch_bundle(self.document, self.client, 'fixture-models', self.root)
        stream.close.assert_called_once()
        self.assertFalse((self.root / MANIFEST).exists())

    def test_existing_immutable_artifact_is_never_overwritten(self):
        path = self.root / self.document['files'][1]['path']
        path.parent.mkdir(parents=True)
        path.write_bytes(b'changed existing artifact')
        with self.assertRaises(ValueError):
            fetch_bundle(self.document, self.client, 'fixture-models', self.root)
        self.assertEqual(path.read_bytes(), b'changed existing artifact')
        self.assertFalse((self.root / MANIFEST).exists())

    @unittest.skipIf(os.name == 'nt', 'Symlink capability checked in the Linux container')
    def test_model_directory_symlink_cannot_escape_application(self):
        with TemporaryDirectory() as outside:
            (self.root / 'model').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                fetch_bundle(self.document, self.client, 'fixture-models', self.root)
            self.assertEqual(list(Path(outside).iterdir()), [])
        self.client.get_object.assert_not_called()

    def test_fetch_command_refuses_student_image_bucket_before_storage_access(self):
        from tools.fetch_v1_lite_bundle import fetch
        config = {'GRAPHISCAN_MODEL_ARTIFACT_BUCKET': 'fixture-images', 'GRAPHISCAN_V1_STORAGE_BUCKET': 'fixture-images'}
        with patch.dict(os.environ, config, clear=True), patch('v1_storage.storage_from_environment') as storage:
            with self.assertRaises(ValueError):
                fetch(self.root / 'descriptor.json')
            storage.assert_not_called()

    def upload_fixture(self):
        from model_bundle import CHUNK_BYTES
        (self.root / 'parts').mkdir()
        for key, content in self.parts.items():
            (self.root / 'parts' / key.removeprefix('sha256/')).write_bytes(content)
        (self.root / 'descriptor.json').write_text(json.dumps(self.document), encoding='utf-8')
        env = {'GRAPHISCAN_V1_SUPABASE_URL': 'https://fixture.example.invalid',
               'GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY': 'sb_publishable_fixture',
               'GRAPHISCAN_V1_SUPABASE_AUTH_SECRET_KEY': 'sb_secret_fixture',
               'GRAPHISCAN_V1_STORAGE_BUCKET': 'fixture-images'}
        state = {'id': 'fixture-models', 'public': False, 'file_size_limit': CHUNK_BYTES,
                 'allowed_mime_types': ['application/octet-stream']}
        session = Mock()
        session.get.return_value = Mock(status_code=200, json=Mock(return_value=state))
        client = Mock()
        client.head_object.side_effect = lambda **request: {'ContentLength': len(self.parts[request['Key']]),
            'Metadata': {'sha256': request['Key'].removeprefix('sha256/')}}
        return env, state, session, client

    def test_uploader_reuses_private_chunks_and_sends_secret_only_as_api_key(self):
        from tools.upload_v1_lite_bundle import upload
        env, _, session, client = self.upload_fixture()
        with patch('v1_storage.storage_from_environment', return_value=SimpleNamespace(client=client)):
            result = upload(self.root, 'fixture-models', env, session)
        self.assertEqual(result['uploaded_chunks'], 0)
        self.assertEqual(result['reused_chunks'], len(self.parts))
        client.put_object.assert_not_called()
        session.post.assert_not_called()
        self.assertEqual(session.get.call_args.kwargs['headers'], {'apikey': 'sb_secret_fixture'})
        self.assertFalse(session.get.call_args.kwargs['allow_redirects'])

    def test_uploader_rejects_public_bucket_before_writing(self):
        from tools.upload_v1_lite_bundle import upload
        env, state, session, client = self.upload_fixture()
        state['public'] = True
        with patch('v1_storage.storage_from_environment', return_value=SimpleNamespace(client=client)), self.assertRaises(ValueError):
            upload(self.root, 'fixture-models', env, session)
        client.head_object.assert_not_called()
        client.put_object.assert_not_called()

    def test_uploader_rejects_changed_local_chunk_before_any_provider_call(self):
        from tools.upload_v1_lite_bundle import upload
        env, _, session, client = self.upload_fixture()
        next((self.root / 'parts').iterdir()).write_bytes(b'changed')
        with patch('v1_storage.storage_from_environment', return_value=SimpleNamespace(client=client)) as storage, self.assertRaises(ValueError):
            upload(self.root, 'fixture-models', env, session)
        storage.assert_not_called()
        session.get.assert_not_called()

    def test_uploader_creates_only_private_binary_bucket_and_verifies_new_objects(self):
        from botocore.exceptions import ClientError
        from model_bundle import CHUNK_BYTES
        from tools.upload_v1_lite_bundle import upload
        env, state, session, client = self.upload_fixture()
        session.get.side_effect = [Mock(status_code=400, json=Mock(return_value={'statusCode': '404'})),
                                  Mock(status_code=200, json=Mock(return_value=state))]
        session.post.return_value = Mock(status_code=201)
        stored = {}
        def head(**request):
            if request['Key'] not in stored:
                raise ClientError({'Error': {'Code': 'NoSuchKey'}}, 'HeadObject')
            content = stored[request['Key']]
            return {'ContentLength': len(content), 'Metadata': {'sha256': hashlib.sha256(content).hexdigest()}}
        def put(**request):
            content = request['Body'].read()
            self.assertEqual(hashlib.sha256(content).hexdigest(), request['Key'].removeprefix('sha256/'))
            self.assertEqual(request['ContentType'], 'application/octet-stream')
            stored[request['Key']] = content
        client.head_object.side_effect = head
        client.put_object.side_effect = put
        with patch('v1_storage.storage_from_environment', return_value=SimpleNamespace(client=client)):
            result = upload(self.root, 'fixture-models', env, session)
        self.assertTrue(result['created_private_bucket'])
        self.assertEqual(result['uploaded_chunks'], len(self.parts))
        self.assertEqual(session.post.call_args.kwargs['json']['public'], False)
        self.assertEqual(session.post.call_args.kwargs['json']['file_size_limit'], CHUNK_BYTES)

    def test_uploader_does_not_treat_other_bad_requests_as_missing_bucket(self):
        from tools.upload_v1_lite_bundle import upload
        env, _, session, client = self.upload_fixture()
        session.get.return_value = Mock(status_code=400, json=Mock(return_value={'statusCode': '403'}))
        with patch('v1_storage.storage_from_environment', return_value=SimpleNamespace(client=client)), self.assertRaises(ValueError):
            upload(self.root, 'fixture-models', env, session)
        session.post.assert_not_called()
        client.head_object.assert_not_called()


if __name__ == '__main__':
    unittest.main()
