"""Server-only S3 adapter. Never constructs public/signed student image URLs."""
import re
from urllib.parse import urlsplit
from api_v1 import BackendUnavailable
from v1_uploads import MAX_BYTES

class PrivateS3Storage:
    def __init__(self,bucket,client):
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}',bucket):raise ValueError('Invalid private bucket.')
        self.bucket,self.client=bucket,client
    def check(self,bucket,key):
        if bucket!=self.bucket or not re.fullmatch(r'screenings/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}\.png',key):raise BackendUnavailable()
    def put(self,bucket,key,data):
        self.check(bucket,key)
        if len(data)>MAX_BYTES:raise BackendUnavailable()
        try:self.client.put_object(Bucket=bucket,Key=key,Body=data,ContentType='image/png',CacheControl='no-store')
        except Exception:raise BackendUnavailable() from None
    def get(self,bucket,key):
        self.check(bucket,key)
        try:
            result=self.client.get_object(Bucket=bucket,Key=key)
            stream=result['Body']
            try:data=stream.read(MAX_BYTES+1)
            finally:stream.close()
            if result.get('ContentType')!='image/png' or not data.startswith(b'\x89PNG\r\n\x1a\n') or len(data)>MAX_BYTES:raise ValueError()
            return data,'image/png'
        except Exception:raise BackendUnavailable() from None
    def delete(self,bucket,key):
        self.check(bucket,key)
        try:self.client.delete_object(Bucket=bucket,Key=key)
        except Exception:raise BackendUnavailable() from None

def storage_from_environment(env):
    names=('GRAPHISCAN_V1_STORAGE_BUCKET','GRAPHISCAN_V1_S3_ENDPOINT','GRAPHISCAN_V1_S3_REGION','GRAPHISCAN_V1_S3_ACCESS_KEY_ID','GRAPHISCAN_V1_S3_SECRET_ACCESS_KEY')
    if not all(env.get(name) for name in names):return None
    try:
        endpoint=urlsplit(env[names[1]])
        project=urlsplit(env['GRAPHISCAN_V1_SUPABASE_URL']).hostname
        expected={project,project.replace('.supabase.co','.storage.supabase.co') if project else None}
        if endpoint.scheme!='https' or endpoint.hostname not in expected or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or endpoint.path!='/storage/v1/s3' or endpoint.port not in (None,443):raise ValueError()
        import boto3
        from botocore.config import Config
        client=boto3.client('s3',endpoint_url=env[names[1]],region_name=env[names[2]],
            aws_access_key_id=env[names[3]],aws_secret_access_key=env[names[4]],
            config=Config(signature_version='s3v4',s3={'addressing_style':'path'},
                retries={'total_max_attempts':1},connect_timeout=5,read_timeout=15,
                request_checksum_calculation='when_required',response_checksum_validation='when_required'))
        return PrivateS3Storage(env[names[0]],client)
    except Exception:return None
