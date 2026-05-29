import uuid

import rasterio
import os

import tempfile

from fastapi import Query, Response
from backend.schemas import RasterPixel, RasterResponse
from sqlalchemy.sql import select
from backend.services.file_storage import get_file_storage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util.typing import Annotated
from backend.database import get_session
from backend.services.file_storage import FileStore
from fastapi import Depends
from backend.models import Raster
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import APIRouter
from uuid import UUID
from rasterio.windows import Window


from backend.services.geotiff_service import GeoTiffService, get_geotiff_service

RASTERS_PREFIX = "/rasters"
COG_REPROJECTED_FILE_NAME = "cog_4326.tif"
ORIGINAL_FILE_NAME = "original.tif"

router = APIRouter(
    prefix=RASTERS_PREFIX,
    tags=["raster"],
)


DbSession = Annotated[AsyncSession, Depends(get_session)]
FileStoreDep = Annotated[FileStore, Depends(get_file_storage)]
GeoTiffServiceDep = Annotated[GeoTiffService, Depends(get_geotiff_service)]


@router.get("/{id}/pixel", operation_id="getPixel")
async def get_raster_pixel(
    id: UUID,
    session: DbSession,
    file_store: FileStoreDep,
    lng: float = Query(ge=-180, le=180),
    lat: float = Query(ge=-90, le=90),
) -> RasterPixel:

    raster = await session.get(Raster, id)

    if raster is None:
        raise HTTPException(status_code=404, detail="File not found")

    raster_file = await file_store.get(
        os.path.join(raster.path, COG_REPROJECTED_FILE_NAME)
    )

    with rasterio.open(raster_file) as dataset:
        row, col = dataset.index(lng, lat)

        # pyrefly: ignore [bad-argument-count]
        window = Window(col, row, 1, 1)

        pixel = dataset.read(window=window)

    return RasterPixel(brightness_values=pixel[:, 0, 0])


@router.get("/{id}", operation_id="getRaster")
async def get_raster(
    id: UUID,
    session: DbSession,
    file_store: FileStoreDep,
    geotiff_service: GeoTiffServiceDep,
) -> Response:
    raster = await session.get(Raster, id)

    if raster is None:
        raise HTTPException(status_code=404, detail="File not found")

    original_file_path = await file_store.get(
        os.path.join(raster.path, COG_REPROJECTED_FILE_NAME)
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        png_file_path = os.path.join(tmp_dir, "png.tif")
        geotiff_service.convert_geotiff_to_png(original_file_path, png_file_path)

        with open(png_file_path, "rb") as f:
            png_bytes = f.read()

    return Response(png_bytes, media_type="image/png")


@router.get("/", operation_id="listRasters")
async def list_rasters(session: DbSession) -> list[RasterResponse]:
    result = await session.execute(select(Raster))
    rasters = result.scalars().all()

    raster_responses: list[RasterResponse] = []

    for raster in rasters:
        bounds = (
            raster.bounding_box_left,
            raster.bounding_box_bottom,
            raster.bounding_box_right,
            raster.bounding_box_top,
        )

        raster_responses.append(
            RasterResponse(
                id=raster.id,
                name=raster.name,
                bounds=bounds,
            )
        )

    return raster_responses


@router.post("/", operation_id="uploadRaster")
async def upload_raster(
    file: UploadFile,
    session: DbSession,
    file_store: FileStoreDep,
    geotiff_service: GeoTiffServiceDep,
) -> RasterResponse:
    id = uuid.uuid4()
    store_path = f"rasters/{id}"

    with tempfile.TemporaryDirectory() as tmp_dir:

        original_file_path = os.path.join(tmp_dir, "original.tif")

        with open(original_file_path, "wb") as f:
            f.write(await file.read())

        # Keep the original data intact. We might want to transform it in some other way in the future
        await file_store.save(
            original_file_path, os.path.join(store_path, ORIGINAL_FILE_NAME)
        )

        reprojected_path = None
        with rasterio.open(original_file_path) as original_dataset:
            if original_dataset.crs.to_epsg() != 4326:
                reprojected_path = os.path.join(tmp_dir, "reprojected.tif")
                geotiff_service.reproject_to_4326(original_file_path, reprojected_path)

        cog_path = os.path.join(tmp_dir, "cog.tif")

        geotiff_service.convert_to_cog(
            reprojected_path if reprojected_path is not None else original_file_path,
            cog_path,
        )

        await file_store.save(
            cog_path, os.path.join(store_path, COG_REPROJECTED_FILE_NAME)
        )

        with rasterio.open(cog_path) as cog_dataset:
            bounds = cog_dataset.bounds

    raster = Raster(
        id=id,
        path=store_path,
        name=file.filename,
        bounding_box_left=bounds.left,
        bounding_box_bottom=bounds.bottom,
        bounding_box_right=bounds.right,
        bounding_box_top=bounds.top,
    )

    response = RasterResponse.from_raster(raster)

    session.add(raster)
    await session.commit()

    return response
