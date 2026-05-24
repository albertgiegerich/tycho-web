from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util.typing import Annotated
from backend.database import get_session
from backend.services.file_storage import FileStorage, LocalFileStorage, S3FileStorage
from fastapi import Depends
from backend.models import FileRecord
from backend.config import settings
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import APIRouter
import uuid

router = APIRouter(
    prefix="/files",
    tags=["files"],
)


DbSession = Annotated[AsyncSession, Depends(get_session)]


def get_file_storage() -> FileStorage:
    if settings.environment == "local":
        return LocalFileStorage()

    return S3FileStorage()


FileStorageDep = Annotated[FileStorage, Depends(get_file_storage)]


@router.post("/")
async def upload(file: UploadFile, session: DbSession, storage: FileStorageDep):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    id = uuid.uuid4()
    path = f"{id}/{id}"

    await storage.save(file, path)

    file_record = FileRecord(id=id, path=path, name=file.filename)
    session.add(file_record)
    await session.commit()

    return {"filename": file.filename}
