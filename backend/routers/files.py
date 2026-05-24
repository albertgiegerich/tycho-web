from sqlalchemy.util.typing import Annotated
from backend.database import get_session
from fastapi import Depends
from backend.database import engine
from backend.models import FileRecord
from sqlalchemy.orm import Session
from backend.config import settings
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import APIRouter
import os

router = APIRouter(
    prefix="/files",
    tags=["files"],
)


DbSession = Annotated[Session, Depends(get_session)]


@router.post("/")
async def upload(file: UploadFile, session: Session = Depends(get_session)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    dest = os.path.join(settings.data_root, file.filename)

    with open(dest, "xb") as f:
        f.write(await file.read())

    file_record = FileRecord(path=file.filename)
    session.add(file_record)
    session.commit()

    return {"filename": file.filename}
