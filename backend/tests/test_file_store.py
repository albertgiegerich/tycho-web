from pathlib import Path
from unittest.mock import patch

import pytest

from backend.services.file_store import LocalFileStore


@pytest.mark.asyncio
async def test_save_copies_file_to_data_root(tmp_path: Path) -> None:
    source_file = tmp_path / "source.tif"
    source_content = b"geotiff data"
    source_file.write_bytes(source_content)

    data_root = tmp_path / "data_root"
    data_root.mkdir()

    with patch("backend.services.file_store.settings") as mock_settings:
        mock_settings.data_root = str(data_root)
        store = LocalFileStore(tmp_dir=str(tmp_path))
        await store.save(str(source_file), "rasters/abc/cog.tif")

    dest = data_root / "rasters" / "abc" / "cog.tif"

    assert dest.exists()
    assert dest.read_bytes() == source_content


@pytest.mark.asyncio
async def test_get_copies_file_to_tmp_dir(tmp_path: Path) -> None:
    data_root = tmp_path / "data_root"
    data_root.mkdir()

    stored_file = data_root / "cog.tif"
    file_content = b"geotiff data"
    stored_file.write_bytes(file_content)

    file_store_tmp_dir = tmp_path / "tmp"
    file_store_tmp_dir.mkdir()

    with patch("backend.services.file_store.settings") as mock_settings:
        mock_settings.data_root = str(data_root)
        store = LocalFileStore(tmp_dir=str(file_store_tmp_dir))
        result = await store.get("cog.tif")

    assert result == str(file_store_tmp_dir / "cog.tif")
    assert Path(result).read_bytes() == file_content


@pytest.mark.asyncio
async def test_delete_removes_file_from_data_root(tmp_path: Path) -> None:
    data_root = tmp_path / "data_root"
    data_root.mkdir()

    stored_file = data_root / "cog.tif"
    stored_file.write_bytes(b"geotiff data")

    assert stored_file.exists()

    with patch("backend.services.file_store.settings") as mock_settings:
        mock_settings.data_root = str(data_root)
        store = LocalFileStore(tmp_dir=str(tmp_path))
        await store.delete("cog.tif")

    assert not stored_file.exists()
