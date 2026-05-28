from backend.services.geotiff_service import get_geotiff_service
from backend.services.geotiff_service import GeoTiffService
from unittest.mock import MagicMock
from backend.models import Raster
from typing import Iterator

from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from unittest.mock import AsyncMock

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


def test_get_raster_not_found(client: TestClient, mock_db_session: AsyncMock) -> None:
    mock_db_session.get.return_value = Raster

    response = client.get(f"/rasters/{EMPTY_UUID}")

    assert response.status_code == 404
