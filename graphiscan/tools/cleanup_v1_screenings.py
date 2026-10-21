"""Bounded failed-upload reconciliation. Does nothing without --apply."""
import argparse
import json
from pathlib import Path
import sys
APP_ROOT=Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:sys.path.insert(0,str(APP_ROOT))

def cleanup(repository,storage):
    from v1_screening_writes import checked_result
    rows=checked_result(repository.execute("SELECT public.graphiscan_screening_cleanup('list',NULL,NULL) AS result",()))['rows']
    report={'status':'cleanup-completed','processed':0,'removed':0,'deferred':0}
    for row in rows:
        success=False
        try:
            bucket,key=row['storage_path'].split('/',1)
            storage.delete(bucket,key);success=True
        except Exception:pass
        checked_result(repository.execute("SELECT public.graphiscan_screening_cleanup('ack',%s::bigint,%s::boolean) AS result",(row['cleanup_id'],success)))
        report['processed']+=1
        report['removed' if success else 'deferred']+=1
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if not args.apply:print(json.dumps({'status':'not-run','writes_attempted':False}));sys.exit(0)
    try:
        from dotenv import load_dotenv
        from v1_backend import backend_from_environment
        load_dotenv(APP_ROOT/'.env')
        service=backend_from_environment().screening_upload_service
        if service.repository is None or service.storage is None:raise ValueError()
        print(json.dumps(cleanup(service.repository,service.storage)))
    except Exception:
        print(json.dumps({'status':'cleanup-unavailable','private_error_omitted':True}));sys.exit(1)
