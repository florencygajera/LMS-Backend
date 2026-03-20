"""
Object storage helpers for S3 or MinIO.
"""

from __future__ import annotations

import io
from urllib.parse import urlparse

import boto3

from core.config import settings


class ObjectStorage:
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )

    def upload_bytes(self, object_key: str, content: bytes, content_type: str) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=content,
            ContentType=content_type,
        )
        return f"s3://{self.bucket}/{object_key}"

    def download_bytes(self, object_uri: str) -> bytes:
        bucket, key = self._parse_uri(object_uri)
        buffer = io.BytesIO()
        self.client.download_fileobj(bucket, key, buffer)
        return buffer.getvalue()

    def generate_presigned_url(self, object_uri: str, expires_in: int = 3600) -> str:
        bucket, key = self._parse_uri(object_uri)
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    @staticmethod
    def _parse_uri(object_uri: str) -> tuple[str, str]:
        parsed = urlparse(object_uri)
        if parsed.scheme != "s3":
            raise ValueError("Object URI must use s3://")
        return parsed.netloc, parsed.path.lstrip("/")


storage = ObjectStorage()





