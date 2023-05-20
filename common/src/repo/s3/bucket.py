import boto3
from botocore.exceptions import ClientError


class Bucket:
    """Bucket incapsulates all operations with S3 Buckets."""
    def __init__(self) -> None:
        self._s3_client = boto3.client("s3")
    
    def put_object(self, bucket: str, object_name: str, body: str) -> None:
        """Put an object in an Amazon S3 bucket."""
        self._s3_client.put_object(Bucket=bucket, Key=object_name, Body=body)
