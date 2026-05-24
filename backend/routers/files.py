from fastapi import Response
from backend.services.geotiff import convert_geotiff_to_png
from backend.schemas import FileRecordResponse
from typing import cast
from sqlalchemy import Sequence
from sqlalchemy.sql import select
from fastapi.responses import FileResponse
from backend.services.file_storage import get_file_storage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util.typing import Annotated
from backend.database import get_session
from backend.services.file_storage import FileStore, LocalFileStore, S3FileStore
from fastapi import Depends
from backend.models import FileRecord
from backend.config import settings
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import APIRouter
import uuid
from uuid import UUID

router = APIRouter(
    prefix="/files",
    tags=["files"],
)


DbSession = Annotated[AsyncSession, Depends(get_session)]


FileStoreDep = Annotated[FileStore, Depends(get_file_storage)]


@router.get("/{id}")
async def get(id: UUID, session: DbSession, file_store: FileStoreDep):
    file_record = await session.get(FileRecord, id)

    if file_record is None:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = await file_store.get(file_record.path)

    file_bytes = convert_geotiff_to_png(file_path)

    return Response(file_bytes)


@router.get("/", response_model=list[FileRecordResponse])
async def get(session: DbSession):
    result = await session.execute(select(FileRecord))
    return result.scalars().all()


@router.post("/")
async def upload(file: UploadFile, session: DbSession, file_store: FileStoreDep):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    id = uuid.uuid4()
    path = f"{id}/{id}"

    await file_store.save(file, path)

    file_record = FileRecord(id=id, path=path, name=file.filename)
    session.add(file_record)
    await session.commit()

    return {"filename": file.filename}
