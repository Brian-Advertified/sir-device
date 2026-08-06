from pathlib import Path
import re
from secrets import token_hex
from typing import BinaryIO

from app.core.errors import ValidationError
from app.domain.ports import StoredFile


_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


class LocalFileStorage:
    def __init__(self, root_directory: str) -> None:
        self._root = Path(root_directory).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

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
        relative = Path(namespace) / f"{token_hex(12)}-{safe_name}"
        destination = (self._root / relative).resolve()
        if self._root not in destination.parents:
            raise ValidationError("Invalid upload path")
        destination.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with destination.open("wb") as output:
            while chunk := source.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    output.close()
                    destination.unlink(missing_ok=True)
                    raise ValidationError("Uploaded file exceeds the configured size limit")
                output.write(chunk)
        return StoredFile(key=str(relative).replace("\\", "/"), size_bytes=total, content_type=content_type)

    def create_download_url(self, key: str, expires_seconds: int = 300) -> str:
        del expires_seconds
        return f"/protected-files/{key}"
