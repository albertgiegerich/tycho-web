from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
from config import settings

app = FastAPI()

origins = ["http://localhost:5173", "localhost:5173"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/uploadfile")
async def create_upload_file(file: UploadFile):

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    dest = os.path.join(settings.data_root, file.filename)

    with open(dest, "xb") as f:
        f.write(await file.read())

    return {"filename": file.filename}
