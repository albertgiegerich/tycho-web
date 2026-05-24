from backend.config import settings
from fastapi import UploadFile
from typing import Protocol
import os


class FileStorage(Protocol):
    async def save(self, file: UploadFile, path: str): ...


class LocalFileStorage(FileStorage):
    async def save(self, file: UploadFile, path: str):

        dest = os.path.join(settings.data_root, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        with open(dest, "xb") as f:
            f.write(await file.read())


class S3FileStorage(FileStorage):
    async def save(self, file: UploadFile, path: str):
        raise NotImplementedError
