from pathlib import Path

from backend.routers.rasters import RASTERS_PREFIX
from backend.services.geotiff_service import get_geotiff_service
from backend.services.geotiff_service import GeoTiffService
from unittest.mock import AsyncMock, MagicMock
from backend.models import Raster
from typing import Iterator
from unittest.mock import patch, mock_open


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


def test_get_raster_returns_png(
    client: TestClient,
    mock_db_session: AsyncMock,
    mock_file_store: AsyncMock,
    mock_geotiff_service: MagicMock,
) -> None:
    raster_path = "raster_path"
    mock_db_session.get.return_value = Raster(path=raster_path)

    original_file_path = "original_file_path"
    mock_file_store.get.return_value = original_file_path

    mock_geotiff_service.get_crs.return_value = "EPSG:4326"

    raster_id = uuid.uuid4()

    png_bytes: bytes = b"png"
    with patch("builtins.open", mock_open(read_data=png_bytes)):
        response = client.get(f"{RASTERS_PREFIX}/{raster_id}")

    mock_db_session.get.assert_called_once_with(Raster, raster_id)

    mock_file_store.get.assert_called_once_with(raster_path)

    mock_geotiff_service.get_crs.assert_called_once_with(original_file_path)

    mock_geotiff_service.reproject_to_4326.assert_not_called()

    args, _ = mock_geotiff_service.convert_geotiff_to_png.call_args
    assert args[0] == original_file_path

    assert Path(args[1]).name == "png.tif"

    assert response.status_code == 200
    assert response.content == png_bytes
    assert response.headers["content-type"] == "image/png"


def test_get_raster_not_found(client: TestClient, mock_db_session: AsyncMock) -> None:
    mock_db_session.get.return_value = None

    response = client.get(f"{RASTERS_PREFIX}/{EMPTY_UUID}")

    assert response.status_code == 404
