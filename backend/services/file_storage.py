from typing import override
import shutil
from typing import Iterator
from backend.config import settings
from fastapi import UploadFile
from typing import Protocol
import os
import tempfile


def get_file_storage() -> Iterator[FileStore]:
    if settings.environment == "local":
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield LocalFileStore(tmp_dir)
    else:
        yield S3FileStore()


class FileStore(Protocol):
    async def save(self, file: UploadFile, path: str): ...
    async def get(self, path: str) -> str: ...


class LocalFileStore(FileStore):
    def __init__(self, tmp_dir: str):
        self.tmp_dir = tmp_dir

    @override
    async def save(self, file: UploadFile, path: str):
        dest = os.path.join(settings.data_root, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        with open(dest, "xb") as f:
            f.write(await file.read())

    @override
    async def get(self, path: str) -> str:
        src = os.path.join(settings.data_root, path)
        dest = os.path.join(self.tmp_dir, os.path.basename(path))
        shutil.copy(src, dest)

        return dest


class S3FileStore(FileStore):
    @override
    async def save(self, file: UploadFile, path: str):
        raise NotImplementedError

    @override
    async def get(self, path: str) -> str:
        raise NotImplementedError
