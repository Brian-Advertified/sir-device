from app.core.config import Settings
from app.core.errors import ConfigurationError
from app.domain.enums import StorageBackend
from app.domain.ports import FileStorage
from app.infrastructure.storage.local_storage import LocalFileStorage
from app.infrastructure.storage.s3_storage import S3FileStorage


def create_file_storage(settings: Settings) -> FileStorage:
    backend = settings.upload_backend.strip().lower()
    if backend == StorageBackend.LOCAL.value:
        return LocalFileStorage(settings.upload_directory)
    if backend == StorageBackend.S3.value:
        return S3FileStorage(bucket=settings.s3_bucket, region=settings.aws_region)
    raise ConfigurationError(f"Unsupported upload backend: {backend}")
