from rasterio.warp import transform_bounds
import os

import tempfile

import rasterio
from fastapi import Response
from backend.schemas import RasterResponse
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
import uuid
from uuid import UUID

from backend.services.geotiff_service import GeoTiffService, get_geotiff_service

RASTERS_PREFIX = "/rasters"

router = APIRouter(
    prefix=RASTERS_PREFIX,
    tags=["raster"],
)


DbSession = Annotated[AsyncSession, Depends(get_session)]
FileStoreDep = Annotated[FileStore, Depends(get_file_storage)]
GeoTiffServiceDep = Annotated[GeoTiffService, Depends(get_geotiff_service)]


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

    original_file_path = await file_store.get(raster.path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        reprojected_file_path = os.path.join(tmp_dir, "reprojected.tif")

        with rasterio.open(original_file_path) as original_dataset:
            if original_dataset.crs == "EPSG:4326":
                reprojected_file_path = original_file_path
            else:
                geotiff_service.reproject_to_4326(
                    original_file_path, reprojected_file_path
                )

        png_file_path = os.path.join(tmp_dir, "png.tif")
        geotiff_service.convert_geotiff_to_png(reprojected_file_path, png_file_path)

        with open(png_file_path, "rb") as f:
            png_bytes = f.read()

    return Response(png_bytes, media_type="image/png")


@router.get("/", operation_id="listRasters")
async def list_rasters(session: DbSession) -> list[RasterResponse]:
    result = await session.execute(select(Raster))
    rasters = result.scalars().all()

    raster_responses: list[RasterResponse] = []

    crs_4326 = "EPSG:4326"

    for raster in rasters:
        bounds = (
            raster.bounding_box_left,
            raster.bounding_box_bottom,
            raster.bounding_box_right,
            raster.bounding_box_top,
        )

        if raster.crs != crs_4326:
            bounds = transform_bounds(raster.crs, crs_4326, *bounds)

        raster_responses.append(
            RasterResponse(
                id=raster.id,
                name=raster.name,
                bounds=bounds,
                crs=crs_4326,
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
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    id = uuid.uuid4()
    store_path = f"{id}/cog.tif"

    with tempfile.TemporaryDirectory() as tmp_dir:
        cog_path = os.path.join(tmp_dir, "cog.tif")

        original_file_path = os.path.join(tmp_dir, "original.tif")
        with open(original_file_path, "wb") as f:
            f.write(await file.read())

        geotiff_service.convert_to_cog(original_file_path, cog_path)

        await file_store.save(cog_path, store_path)

        with rasterio.open(cog_path) as dataset:
            bounds = dataset.bounds
            crs = dataset.crs.to_string()

    raster = Raster(
        id=id,
        path=store_path,
        name=file.filename,
        bounding_box_left=bounds.left,
        bounding_box_bottom=bounds.bottom,
        bounding_box_right=bounds.right,
        bounding_box_top=bounds.top,
        crs=crs,
    )

    response = RasterResponse.from_raster(raster)

    session.add(raster)
    await session.commit()

    return response
