"""Prepare private model chunks locally; never uploads or reads configuration."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model_bundle import prepare_bundle

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT.parent / '.local-tools/model-bundle')
    args = parser.parse_args()
    try:
        document = prepare_bundle(ROOT, args.output_dir)
        print(json.dumps({'status': 'private-model-bundle-prepared', 'files': len(document['files']),
                          'bytes': sum(item['size'] for item in document['files']),
                          'uploaded': False, 'configuration_read': False}))
    except Exception as failure:
        print(json.dumps({'status': 'private-model-bundle-not-prepared', 'error_type': type(failure).__name__}))
        sys.exit(1)
