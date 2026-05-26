import rasterio
from fastapi import Response
from backend.services.geotiff import convert_geotiff_to_png
from backend.schemas import RasterResponse
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
from backend.models import Raster
from backend.config import settings
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import APIRouter
import uuid
from uuid import UUID

router = APIRouter(
    prefix="/rasters",
    tags=["raster"],
)


DbSession = Annotated[AsyncSession, Depends(get_session)]


FileStoreDep = Annotated[FileStore, Depends(get_file_storage)]


@router.get("/{id}", operation_id="getRaster")
async def get(id: UUID, session: DbSession, file_store: FileStoreDep):
    raster = await session.get(Raster, id)

    if raster is None:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = await file_store.get(raster.path)

    file_bytes = convert_geotiff_to_png(file_path)

    return Response(file_bytes, media_type="image/png")


@router.get("/", response_model=list[RasterResponse], operation_id="listRasters")
async def get(session: DbSession):
    result = await session.execute(select(Raster))
    rasters = result.scalars().all()

    return map(
        lambda f: RasterResponse(
            id=f.id,
            name=f.name,
            bounds=(
                f.bounding_box_left,
                f.bounding_box_bottom,
                f.bounding_box_right,
                f.bounding_box_top,
            ),
            crs=f.crs,
        ),
        rasters,
    )


@router.post("/", operation_id="uploadRaster")
async def upload(file: UploadFile, session: DbSession, file_store: FileStoreDep):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    id = uuid.uuid4()
    path = f"{id}/{id}"

    await file_store.save(file, path)

    raster_path = await file_store.get(path)

    with rasterio.open(raster_path) as dataset:
        bounds = dataset.bounds
        crs = dataset.crs.to_string()

    raster = Raster(
        id=id,
        path=path,
        name=file.filename,
        bounding_box_left=bounds.left,
        bounding_box_bottom=bounds.bottom,
        bounding_box_right=bounds.right,
        bounding_box_top=bounds.top,
        crs=crs,
    )
    session.add(raster)
    await session.commit()

    return {"filename": file.filename}
