"""Fetch private model files at build time using existing server-only S3 keys."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def fetch(descriptor):
    from model_bundle import fetch_bundle
    from v1_lite_models import LiteBinaryRuntime
    from v1_storage import storage_from_environment
    bucket = os.environ.get('GRAPHISCAN_MODEL_ARTIFACT_BUCKET', '')
    if not bucket or bucket == os.environ.get('GRAPHISCAN_V1_STORAGE_BUCKET'):
        raise ValueError('Use a separate private model-artifact bucket')
    storage = storage_from_environment(os.environ)
    if storage is None:
        raise ValueError('Configure existing trusted-project S3 transport')
    if descriptor.stat().st_size > 65536:
        raise ValueError('Oversized model bundle descriptor')
    document = json.loads(descriptor.read_text(encoding='utf-8'))
    manifest = fetch_bundle(document, storage.client, bucket, ROOT)
    runtime = LiteBinaryRuntime(manifest)
    return {'status': 'private-model-bundle-ready', 'models': len(runtime.entries), 'tensorflow_imported': 'tensorflow' in sys.modules}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--descriptor', type=Path, default=ROOT / 'model/litert-bundle.json')
    args = parser.parse_args()
    try:
        print(json.dumps(fetch(args.descriptor)))
    except Exception as failure:
        # S3/HTTP exceptions can include request details; never print their values.
        print(json.dumps({'status': 'private-model-bundle-not-ready', 'error_type': type(failure).__name__}))
        sys.exit(1)
