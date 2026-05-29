import os
import io
import boto3
from botocore.config import Config

class R2Storage:
    def __init__(self):
        self.account_id = os.environ.get('R2_ACCOUNT_ID', '')
        self.access_key = os.environ.get('R2_ACCESS_KEY', '')
        self.secret_key = os.environ.get('R2_SECRET_KEY', '')
        self.bucket = os.environ.get('R2_BUCKET', 'statclean')
        self.public_url = os.environ.get('R2_PUBLIC_URL', '')
        self.enabled = all([self.account_id, self.access_key, self.secret_key])

        if self.enabled:
            self.client = boto3.client(
                's3',
                endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version='s3v4'),
                region_name='auto',
            )

    def upload(self, filepath, key):
        if not self.enabled:
            return False
        self.client.upload_file(filepath, self.bucket, key)
        return True

    def upload_bytes(self, data, key, content_type='application/octet-stream'):
        if not self.enabled:
            return False
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return True

    def download(self, key, filepath):
        if not self.enabled:
            return False
        self.client.download_file(self.bucket, key, filepath)
        return True

    def download_bytes(self, key):
        if not self.enabled:
            return None
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj['Body'].read()

    def delete(self, key):
        if not self.enabled:
            return False
        self.client.delete_object(Bucket=self.bucket, Key=key)
        return True

    def presigned_url(self, key, expires=3600):
        if not self.enabled:
            return None
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires,
        )

    def list(self, prefix=''):
        if not self.enabled:
            return []
        objs = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [o['Key'] for o in objs.get('Contents', [])]

r2 = R2Storage()
