from backend.config import settings
from backend.schemas import GetRasterRequest
from backend.services.raster_operation_service import (
    get_raster_operation_service,
)

import tempfile
import uuid

from rasterio.windows import Window
from sqlalchemy import select
from backend.models import RasterFileName

import rasterio

from fastapi import Body, Query, Response, UploadFile
from backend.schemas import RasterPixel, RasterResponse
from backend.services.file_store import get_file_store
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util.typing import Annotated
from backend.database import get_session
from backend.services.file_store import FileStore
from fastapi import Depends
from backend.models import Raster
from fastapi import HTTPException
from fastapi import APIRouter
from uuid import UUID


from backend.services.geotiff_service import GeoTiffService, get_geotiff_service
from backend.services.raster_operation_service import RasterOperationService
from backend.utils import normalize_0_to_1

RASTERS_PREFIX = "/rasters"

router = APIRouter(
    prefix=RASTERS_PREFIX,
    tags=["raster"],
)


DbSession = Annotated[AsyncSession, Depends(get_session)]

FileStoreDep = Annotated[FileStore, Depends(get_file_store)]

GeoTiffServiceDep = Annotated[GeoTiffService, Depends(get_geotiff_service)]

RasterOperationServiceDep = Annotated[
    RasterOperationService, Depends(get_raster_operation_service)
]


@router.get("/{id}/pixel", operation_id="getPixel")
async def get_raster_pixel(
    id: UUID,
    session: DbSession,
    lng: float = Query(ge=-180, le=180),
    lat: float = Query(ge=-90, le=90),
) -> RasterPixel:

    raster = await session.get(Raster, id)

    if raster is None:
        raise HTTPException(status_code=404, detail="File not found")

    with rasterio.open(f"{raster.path}/{RasterFileName.COG.value}") as dataset:
        row, col = dataset.index(lng, lat)

        # pyrefly: ignore [bad-argument-count]
        window = Window(col, row, 1, 1)

        pixel = dataset.read(window=window)

    return RasterPixel(brightness_values=pixel[:, 0, 0], row=row, col=col)


@router.post("/{id}", operation_id="getRaster")
async def get_raster(
    id: UUID,
    session: DbSession,
    geotiff_service: GeoTiffServiceDep,
    raster_operation_service: RasterOperationServiceDep,
    request_payload: GetRasterRequest = Body(),
) -> Response:
    raster = await session.get(Raster, id)

    if raster is None:
        raise HTTPException(status_code=404, detail="File not found")

    path = f"{settings.data_root}/{raster.path}/{RasterFileName.COG.value}"

    with tempfile.TemporaryDirectory() as tmp_dir:

        with rasterio.open(path) as dataset:
            raster_image = dataset.read(request_payload.band_order)

            raster_image = normalize_0_to_1(raster_image)

            if request_payload.contrast_enhancement:
                raster_image = raster_operation_service.apply_contrast_enhancement(
                    raster_image, request_payload.contrast_enhancement
                )

            if request_payload.operations:
                raster_image = raster_operation_service.apply_operations(
                    raster_image, request_payload.operations
                )

            png_file_path = f"{tmp_dir}/png.tif"
            geotiff_service.save_as_png(raster_image, png_file_path)

            with open(png_file_path, "rb") as f:
                png_bytes = f.read()

    return Response(png_bytes, media_type="image/png")


@router.delete("/{id}", operation_id="deleteRaster", status_code=204)
async def delete_raster(
    id: UUID,
    session: DbSession,
    file_store: FileStoreDep,
):
    raster = await session.get(Raster, id)

    if raster is None:
        raise HTTPException(status_code=404, detail="Raster not found")

    for file_name in RasterFileName:
        await file_store.delete(f"{raster.path}/{file_name.value}")

    await session.delete(raster)
    await session.commit()


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
                band_count=raster.band_count,
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

        original_file_path = f"{tmp_dir}/original.tif"

        with open(original_file_path, "wb") as f:
            f.write(await file.read())

        # Keep the original data intact. We might want to transform it in some other way in the future
        await file_store.save(
            original_file_path, f"{store_path}/{RasterFileName.ORIGINAL.value}"
        )

        reprojected_path = None
        with rasterio.open(original_file_path) as original_dataset:
            band_count: int = original_dataset.count

            if original_dataset.crs.to_epsg() == 4326:
                reprojected_path = original_file_path
            else:
                reprojected_path = f"{tmp_dir}/reprojected.tif"
                geotiff_service.reproject_to_4326(original_file_path, reprojected_path)

        cog_path = f"{tmp_dir}/cog.tif"

        geotiff_service.convert_to_cog(
            reprojected_path,
            cog_path,
        )

        await file_store.save(cog_path, f"{store_path}/{RasterFileName.COG.value}")

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
        band_count=band_count,
    )

    response = RasterResponse.from_raster(raster)

    session.add(raster)
    await session.commit()

    return response
