"""Explicit synthetic Storage probe: one generated PNG, no application records."""
import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import sys
from urllib.parse import quote, urlsplit
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v1_storage import storage_from_environment


def run(apply=False):
    report={'status':'not-run','checks':[],'synthetic_object_only':True,'application_database_writes':False}
    if not apply:return report
    from PIL import Image
    import requests
    storage=storage_from_environment(os.environ)
    def check(name,passed):
        report['checks'].append({'name':name,'status':'pass' if passed else 'fail'})
        return passed
    if not check('storage_configured',storage is not None):report['status']='blocked';return report
    receipt=ROOT/'model/storage-check.local'
    key='screenings/'+str(uuid4())+'.png'
    attempted=False
    try:
        # Retain a local cleanup locator before any uncertain provider write.
        with receipt.open('x',encoding='utf-8') as stream:
            json.dump({'purpose':'graphiscan-synthetic-storage-check-v1','bucket':storage.bucket,'key':key},stream)
        attempted=True
        output=BytesIO();Image.new('RGB',(32,32),'white').save(output,format='PNG');data=output.getvalue()
        storage.put(storage.bucket,key,data);check('synthetic_png_uploaded',True)
        downloaded,mime=storage.get(storage.bucket,key)
        check('authenticated_download_matches',downloaded==data and mime=='image/png')
        origin=os.environ.get('GRAPHISCAN_V1_SUPABASE_URL','').rstrip('/')
        parsed=urlsplit(origin)
        if parsed.scheme!='https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError()
        with requests.Session() as session:
            session.trust_env=False
            with session.get(origin+'/storage/v1/object/public/'+quote(storage.bucket,safe='')+'/'+quote(key,safe='/'),
                             timeout=(5,15),allow_redirects=False,stream=True) as response:
                check('anonymous_public_route_denied',response.status_code in (400,403,404))
    except Exception:
        check('storage_probe_completed',False)
    finally:
        if attempted:
            cleaned=False
            try:
                storage.delete(storage.bucket,key)
                try:storage.client.head_object(Bucket=storage.bucket,Key=key)
                except Exception as error:
                    details=getattr(error,'response',{})
                    cleaned=details.get('ResponseMetadata',{}).get('HTTPStatusCode')==404 and details.get('Error',{}).get('Code') in ('404','NoSuchKey','NotFound')
                if cleaned:receipt.unlink()
            except Exception:pass
            check('synthetic_object_deleted_and_missing',cleaned)
        report['status']='storage-io-check-passed' if report['checks'] and all(row['status']=='pass' for row in report['checks']) else 'failed'
    return report


if __name__=='__main__':
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    report=run(parser.parse_args().apply);print(json.dumps(report,indent=2))
    sys.exit(0 if report['status'] in ('not-run','storage-io-check-passed') else 1)
