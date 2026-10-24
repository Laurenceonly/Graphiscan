"""Upload reviewed model chunks to a separate private bucket in the existing project."""
import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

class ProvisioningError(ValueError):
    def __init__(self, code, http_status=None):
        self.code, self.http_status = code, http_status
        super().__init__(code)


def upload(folder, bucket, env, session=None):
    from botocore.exceptions import ClientError
    import requests
    from model_bundle import CHUNK_BYTES, validate_descriptor
    from v1_backend import SupabaseIdentityVerifier
    from v1_storage import storage_from_environment
    from v1_uploads import file_digest

    if not isinstance(bucket, str) or re.fullmatch('[a-z0-9][a-z0-9_-]{0,62}', bucket) is None or bucket == env.get('GRAPHISCAN_V1_STORAGE_BUCKET'):
        raise ValueError('Use a separate private model bucket')
    folder = folder.resolve()
    descriptor = folder / 'descriptor.json'
    if descriptor.stat().st_size > 65536:
        raise ValueError('Oversized model descriptor')
    document = json.loads(descriptor.read_text(encoding='utf-8'))
    files = validate_descriptor(document)
    parts_root = (folder / 'parts').resolve()
    if not parts_root.is_relative_to(folder):
        raise ValueError('Private parts folder escapes bundle')
    chunks = {}
    for item in files:
        for part in item['parts']:
            path = (parts_root / part['sha256']).resolve()
            if not path.is_relative_to(parts_root) or path.stat().st_size != part['size'] or file_digest(path) != part['sha256']:
                raise ValueError('Local private chunk changed')
            if part['sha256'] in chunks and chunks[part['sha256']][1] != part['size']:
                raise ValueError('Private chunk size conflict')
            chunks[part['sha256']] = (path, part['size'])
    # Reuse the established HTTPS/project validation before sending any secret.
    verifier = SupabaseIdentityVerifier(env.get('GRAPHISCAN_V1_SUPABASE_URL', ''),
                                       env.get('GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY', ''))
    storage = storage_from_environment(env)
    secret = env.get('GRAPHISCAN_V1_SUPABASE_AUTH_SECRET_KEY', '')
    if storage is None:
        raise ProvisioningError('existing_s3_configuration_unavailable')
    if not secret.startswith('sb_secret_'):
        raise ProvisioningError('existing_server_secret_key_unavailable')
    session = session if session is not None else requests.Session()
    headers = {'apikey': secret}  # New Supabase secret keys are not bearer JWTs.
    url = verifier.origin + '/storage/v1/bucket/' + bucket

    def bucket_state():
        response = session.get(url, headers=headers, timeout=(5, 20), allow_redirects=False)
        try:
            if response.status_code == 404:
                return None
            if response.status_code == 400:
                # Storage can wrap its structured 404 in HTTP400. Other400
                # responses remain errors and must never trigger creation.
                body = response.json()
                if isinstance(body, dict) and body.get('statusCode') in (404, '404'):
                    return None
            if response.status_code != 200:
                raise ProvisioningError('private_bucket_lookup_failed', response.status_code)
            return response.json()
        finally:
            response.close()

    state = bucket_state()
    created = False
    if state is None:
        response = session.post(verifier.origin+'/storage/v1/bucket', headers=headers,
            json={'id': bucket, 'name': bucket, 'public': False,
                  'file_size_limit': CHUNK_BYTES, 'allowed_mime_types': ['application/octet-stream']},
            timeout=(5, 20), allow_redirects=False)
        try:
            if response.status_code not in (200, 201, 409):
                raise ProvisioningError('private_bucket_creation_failed', response.status_code)
            created = response.status_code in (200, 201)
        finally:
            response.close()
        state = bucket_state()
    if (not isinstance(state, dict) or state.get('id') != bucket or state.get('public') is not False
            or type(state.get('file_size_limit')) is not int or state['file_size_limit'] < CHUNK_BYTES
            or state.get('allowed_mime_types') != ['application/octet-stream']):
        raise ProvisioningError('private_bucket_configuration_mismatch')
    uploaded = reused = 0
    for digest, (path, size) in sorted(chunks.items()):
        key = 'sha256/' + digest
        try:
            existing = storage.client.head_object(Bucket=bucket, Key=key)
        except ClientError as failure:
            if failure.response.get('Error', {}).get('Code') not in ('404', 'NoSuchKey', 'NotFound'):
                raise
            existing = None
        if existing is None:
            with path.open('rb') as stream:
                storage.client.put_object(Bucket=bucket, Key=key, Body=stream, ContentLength=size,
                    ContentType='application/octet-stream', CacheControl='no-store', Metadata={'sha256': digest})
            existing = storage.client.head_object(Bucket=bucket, Key=key)
            uploaded += 1
        else:
            reused += 1
        if existing.get('ContentLength') != size or existing.get('Metadata', {}).get('sha256') != digest:
            raise ValueError('Existing remote artifact identity conflict')
    return {'status': 'private-model-bundle-uploaded', 'files': len(files), 'chunks': len(chunks),
            'uploaded_chunks': uploaded, 'reused_chunks': reused, 'created_private_bucket': created,
            'bytes': sum(item['size'] for item in files), 'live_api_changed': False, 'schema_changed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle-dir', type=Path, default=ROOT.parent / '.local-tools/model-bundle')
    parser.add_argument('--bucket', required=True)
    args = parser.parse_args()
    try:
        from dotenv import dotenv_values
        environment = {**dotenv_values(ROOT / '.env'), **os.environ}
        print(json.dumps(upload(args.bundle_dir, args.bucket, environment)))
    except ProvisioningError as failure:
        print(json.dumps({'status': 'private-model-bundle-not-uploaded', 'error_code': failure.code,
                          'http_status': failure.http_status, 'private_error_omitted': True}))
        sys.exit(1)
    except Exception as failure:
        print(json.dumps({'status': 'private-model-bundle-not-uploaded', 'error_type': type(failure).__name__,
                          'private_error_omitted': True}))
        sys.exit(1)
