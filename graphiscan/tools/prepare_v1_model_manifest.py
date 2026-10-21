"""Hash the existing trusted artifact; does not publish/approve model evidence."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from v1_uploads import PREPROCESSING_KEY,file_digest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-key',required=True);parser.add_argument('--model-version',required=True)
    args=parser.parse_args()
    try:
        if not args.model_key.strip() or not args.model_version.strip():raise ValueError()
        manifest={'model_key':args.model_key.strip(),'model_version':args.model_version.strip(),
            'preprocessing_key':PREPROCESSING_KEY,'artifact_sha256':file_digest(ROOT/'model/graphiscan_model.keras'),
            'class_names_sha256':file_digest(ROOT/'model/class_names.json'),'runtime_source_sha256':file_digest(ROOT/'predict.py')}
        destination=ROOT/'model/deployment.local.json'
        # Refuse to overwrite a pinned identity silently.
        with destination.open('x',encoding='utf-8') as stream:stream.write(json.dumps(manifest,indent=2)+'\n')
        from dotenv import set_key
        set_key(str(ROOT/'.env'),'GRAPHISCAN_V1_MODEL_MANIFEST',destination.as_posix())
        print(json.dumps({'status':'model-manifest-prepared','configuration_saved':True,'evaluation_verified':False,'registry_changed':False}))
    except Exception:
        print(json.dumps({'status':'model-manifest-not-confirmed','private_error_omitted':True}));sys.exit(1)
