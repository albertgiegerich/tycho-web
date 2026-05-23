from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
from config import settings
from sqlalchemy.engine import URL

APP_DATABASE_URL = URL.create(
    drivername="postgresql",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)


from sqlalchemy import create_engine

app = FastAPI()

origins = ["http://localhost:5173", "localhost:5173"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_engine = create_engine(APP_DATABASE_URL)


@app.post("/uploadfile")
async def create_upload_file(file: UploadFile):

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    dest = os.path.join(settings.data_root, file.filename)

    with open(dest, "xb") as f:
        f.write(await file.read())

    return {"filename": file.filename}
