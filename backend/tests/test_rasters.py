from rasterio.coords import BoundingBox
import os
from pathlib import Path

from backend.routers.rasters import RASTERS_PREFIX
from backend.services.geotiff_service import get_geotiff_service
from backend.services.geotiff_service import GeoTiffService
from unittest.mock import AsyncMock, MagicMock
from pytest_mock import MockerFixture
from backend.models import Raster
from typing import Iterator
from unittest.mock import mock_open


from sqlalchemy.ext.asyncio import AsyncSession
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.database import get_session
from backend.services.file_storage import FileStore, get_file_storage


@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_file_store() -> AsyncMock:
    return AsyncMock(spec=FileStore)


@pytest.fixture
def mock_geotiff_service() -> MagicMock:
    return MagicMock(spec=GeoTiffService)


@pytest.fixture
def client(
    mock_db_session: AsyncMock,
    mock_file_store: AsyncMock,
    mock_geotiff_service: MagicMock,
) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_file_storage] = lambda: mock_file_store
    app.dependency_overrides[get_geotiff_service] = lambda: mock_geotiff_service

    yield TestClient(app)

    app.dependency_overrides.clear()


EMPTY_UUID = uuid.UUID(int=0)


def test_get_raster(
    client: TestClient,
    mock_db_session: AsyncMock,
    mock_file_store: AsyncMock,
    mock_geotiff_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    raster_path = "raster_path"
    mock_db_session.get.return_value = Raster(path=raster_path)

    original_file_path = "original_file_path"
    mock_file_store.get.return_value = original_file_path

    raster_id = uuid.uuid4()

    mock_rasterio_dataset = mocker.MagicMock()
    mock_rasterio_dataset.crs = 4326

    png_bytes: bytes = b"png"
    mock_rasterio_open = mocker.patch(
        "backend.routers.rasters.rasterio.open", autospec=True
    )
    mock_rasterio_open.return_value.__enter__.return_value = mock_rasterio_dataset
    mocker.patch("backend.routers.rasters.open", mock_open(read_data=png_bytes))

    response = client.get(f"{RASTERS_PREFIX}/{raster_id}")

    mock_db_session.get.assert_called_once_with(Raster, raster_id)
    mock_file_store.get.assert_called_once_with(raster_path)
    mock_rasterio_open.assert_called_once_with(original_file_path)
    mock_geotiff_service.reproject_to_4326.assert_not_called()

    args, _ = mock_geotiff_service.convert_geotiff_to_png.call_args
    assert args[0] == original_file_path
    assert Path(args[1]).name == "png.tif"

    assert response.status_code == 200
    assert response.content == png_bytes
    assert response.headers["content-type"] == "image/png"


def test_get_raster_reprojects_if_not_4326(
    client: TestClient,
    mock_db_session: AsyncMock,
    mock_file_store: AsyncMock,
    mock_geotiff_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    mock_db_session.get.return_value = Raster()

    original_file_path = "original_file_path"
    mock_file_store.get.return_value = original_file_path

    mock_rasterio_dataset = mocker.MagicMock()
    mock_rasterio_dataset.crs = 9999

    mock_rasterio_open = mocker.patch(
        "backend.routers.rasters.rasterio.open", autospec=True
    )
    mock_rasterio_open.return_value.__enter__.return_value = mock_rasterio_dataset
    mocker.patch("backend.routers.rasters.open", mock_open(read_data=b""))

    response = client.get(f"{RASTERS_PREFIX}/{EMPTY_UUID}")

    reproject_to_4326_args, _ = mock_geotiff_service.reproject_to_4326.call_args

    assert reproject_to_4326_args[0] == original_file_path
    assert Path(reproject_to_4326_args[1]).name == "reprojected.tif"

    convert_geotiff_to_png_args, _ = (
        mock_geotiff_service.convert_geotiff_to_png.call_args
    )
    assert Path(convert_geotiff_to_png_args[0]).name == "reprojected.tif"

    assert Path(convert_geotiff_to_png_args[1]).name == "png.tif"

    assert response.status_code == 200


def test_list_rasters(
    client: TestClient, mock_db_session: AsyncMock, mocker: MockerFixture
) -> None:
    raster_id = uuid.uuid4()
    raster = Raster(
        id=raster_id,
        name="test.tif",
        crs=4326,
        bounding_box_left=1.0,
        bounding_box_bottom=2.0,
        bounding_box_right=3.0,
        bounding_box_top=4.0,
    )
    mock_result = mocker.MagicMock()
    mock_result.scalars.return_value.all.return_value = [raster]
    mock_db_session.execute.return_value = mock_result

    response = client.get(f"{RASTERS_PREFIX}/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0] == {
        "id": str(raster_id),
        "name": "test.tif",
        "bounds": [1.0, 2.0, 3.0, 4.0],
        "crs": 4326,
    }


def test_list_rasters_reprojects_bounds_if_not_4326(
    client: TestClient, mock_db_session: AsyncMock, mocker: MockerFixture
) -> None:
    raster_id = uuid.uuid4()
    raster = Raster(
        id=raster_id,
        name="test.tif",
        crs=32615,
        bounding_box_left=1.0,
        bounding_box_bottom=2.0,
        bounding_box_right=3.0,
        bounding_box_top=4.0,
    )
    mock_result = mocker.MagicMock()
    mock_result.scalars.return_value.all.return_value = [raster]
    mock_db_session.execute.return_value = mock_result

    transformed_bounds = (10.0, 20.0, 30.0, 40.0)

    mocker.patch(
        "backend.routers.rasters.transform_bounds", return_value=transformed_bounds
    )

    response = client.get(f"{RASTERS_PREFIX}/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0] == {
        "id": str(raster_id),
        "name": "test.tif",
        "bounds": list(transformed_bounds),
        "crs": 4326,
    }


def test_upload_raster(
    client: TestClient,
    mock_db_session: AsyncMock,
    mock_file_store: AsyncMock,
    mock_geotiff_service: MagicMock,
    mocker: MockerFixture,
) -> None:

    fixed_id = uuid.UUID(int=1)
    mocker.patch("backend.routers.rasters.uuid.uuid4", return_value=fixed_id)

    fake_tmp_path = "tmp"

    mock_tmp = mocker.MagicMock()
    mock_tmp.__enter__.return_value = fake_tmp_path
    mocker.patch(
        "backend.routers.rasters.tempfile.TemporaryDirectory", return_value=mock_tmp
    )

    mock_open_write = mock_open()
    mocker.patch("backend.routers.rasters.open", mock_open_write)

    mock_rasterio_open = mocker.MagicMock()
    mock_dataset = mocker.MagicMock()

    mock_crs = mocker.MagicMock()
    mock_crs.to_epsg.return_value = 9999

    mock_dataset.crs = mock_crs
    mock_dataset.bounds = BoundingBox(left=1, bottom=2, right=3, top=4)

    mock_rasterio_open.return_value.__enter__.return_value = mock_dataset
    mocker.patch("backend.routers.rasters.rasterio.open", mock_rasterio_open)

    geotiff_data = b"geotiff data"

    response = client.post(
        f"{RASTERS_PREFIX}/",
        files={"file": ("test.tif", geotiff_data)},
    )

    original_path = os.path.join(fake_tmp_path, "original.tif")
    mock_open_write.assert_called_once_with(original_path, "wb")

    mock_open_write.return_value.__enter__.return_value.write.assert_called_once_with(
        geotiff_data
    )

    cog_path = os.path.join(fake_tmp_path, "cog.tif")
    mock_geotiff_service.convert_to_cog.assert_called_once_with(original_path, cog_path)

    save_args, _ = mock_file_store.save.call_args

    assert Path(save_args[0]).name == "cog.tif"
    assert save_args[1] == f"rasters/{fixed_id}/cog.tif"

    mock_db_session.add.assert_called_once()
    added_raster = mock_db_session.add.call_args.args[0]

    assert added_raster.id == fixed_id
    assert added_raster.path == f"rasters/{fixed_id}/cog.tif"
    assert added_raster.name == "test.tif"
    assert added_raster.bounding_box_left == 1
    assert added_raster.bounding_box_bottom == 2
    assert added_raster.bounding_box_right == 3
    assert added_raster.bounding_box_top == 4
    assert added_raster.crs == 9999

    mock_db_session.commit.assert_called_once()

    assert response.status_code == 200
    assert response.json() == {
        "id": str(fixed_id),
        "name": "test.tif",
        "bounds": [1.0, 2.0, 3.0, 4.0],
        "crs": 9999,
    }


def test_get_raster_not_found(client: TestClient, mock_db_session: AsyncMock) -> None:
    mock_db_session.get.return_value = None

    response = client.get(f"{RASTERS_PREFIX}/{EMPTY_UUID}")

    assert response.status_code == 404
