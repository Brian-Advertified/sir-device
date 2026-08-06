from pathlib import Path
import re
from secrets import token_hex
from typing import BinaryIO

import boto3

from app.core.errors import ConfigurationError, ValidationError
from app.domain.ports import StoredFile


_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


class S3FileStorage:
    def __init__(self, *, bucket: str | None, region: str) -> None:
        if not bucket:
            raise ConfigurationError("S3_BUCKET is required when UPLOAD_BACKEND=s3")
        self._bucket = bucket
        self._client = boto3.client("s3", region_name=region)

    def save(
        self,
        *,
        source: BinaryIO,
        original_name: str,
        content_type: str,
        namespace: str,
        max_bytes: int,
    ) -> StoredFile:
        safe_name = _SAFE_NAME.sub("-", Path(original_name).name).strip(".-") or "upload"
        key = f"{namespace}/{token_hex(12)}-{safe_name}"
        contents = source.read(max_bytes + 1)
        if len(contents) > max_bytes:
            raise ValidationError("Uploaded file exceeds the configured size limit")
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=contents,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        return StoredFile(key=key, size_bytes=len(contents), content_type=content_type)

    def create_download_url(self, key: str, expires_seconds: int = 300) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )
