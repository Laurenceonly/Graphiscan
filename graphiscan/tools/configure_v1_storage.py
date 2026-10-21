"""Local hidden-prompt Storage setup. Does not create buckets or contact Supabase."""
import getpass
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from dotenv import load_dotenv,set_key

def configure():
    if not sys.stdin.isatty():raise ValueError()
    root=Path(__file__).resolve().parents[1];env_file=root/'.env';load_dotenv(env_file)
    project=urlsplit(os.environ.get('GRAPHISCAN_V1_SUPABASE_URL','')).hostname
    if not project:raise ValueError()
    bucket=input('Existing PRIVATE bucket ID: ').strip()
    endpoint=input('S3 endpoint from this project settings (HTTPS): ').strip()
    region=input('S3 region from this project settings: ').strip()
    access=getpass.getpass('Server S3 Access Key ID (hidden): ')
    secret=getpass.getpass('Server S3 Secret Access Key (hidden): ')
    parsed=urlsplit(endpoint)
    if (not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}',bucket) or
        not re.fullmatch(r'[a-z0-9-]{1,64}',region) or parsed.scheme!='https' or
        parsed.hostname not in {project,project.replace('.supabase.co','.storage.supabase.co')} or
        parsed.path!='/storage/v1/s3' or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.port not in (None,443)):
        raise ValueError()
    if not 8<=len(access)<=256 or not 16<=len(secret)<=4096 or any(not 33<=ord(c)<=126 for c in access+secret):raise ValueError()
    for key,value in {'GRAPHISCAN_V1_STORAGE_BUCKET':bucket,'GRAPHISCAN_V1_S3_ENDPOINT':endpoint,
        'GRAPHISCAN_V1_S3_REGION':region,'GRAPHISCAN_V1_S3_ACCESS_KEY_ID':access,'GRAPHISCAN_V1_S3_SECRET_ACCESS_KEY':secret}.items():set_key(str(env_file),key,value)
    print(json.dumps({'status':'storage-configuration-saved','connection_tested':False,'bucket_created':False,'database_changed':False}))

if __name__=='__main__':
    try:configure()
    except (Exception,KeyboardInterrupt):
        print(json.dumps({'status':'storage-configuration-not-confirmed','private_error_omitted':True}));sys.exit(1)
