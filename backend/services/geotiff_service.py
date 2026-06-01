import numpy as np
import rasterio
import numpy.typing as npt
from rasterio.enums import Resampling
from rasterio.shutil import copy
from rasterio.warp import calculate_default_transform, reproject

from backend.utils import get_dtype_min_max


def get_geotiff_service() -> GeoTiffService:
    return GeoTiffService()


class GeoTiffService:
    def save_as_png(self, rgb: npt.NDArray[np.float64], png_file_path: str) -> None:

        scaled_to_int8 = rgb * np.iinfo(np.uint8).max

        with rasterio.open(
            png_file_path,
            mode="w",
            driver="PNG",
            height=scaled_to_int8.shape[1],
            width=scaled_to_int8.shape[2],
            count=3,
            dtype=np.uint8,
        ) as png_dataset:
            png_dataset.write(scaled_to_int8)

    def reproject_to_4326(self, src_file_path: str, dest_file_path: str) -> None:
        dst_crs = "EPSG:4326"

        with rasterio.open(src_file_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )
            kwargs = src.meta.copy()
            kwargs.update(
                {
                    "crs": dst_crs,
                    "transform": transform,
                    "width": width,
                    "height": height,
                }
            )

            with rasterio.open(dest_file_path, "w", **kwargs) as dst:
                bands = list(range(1, src.count + 1))
                reproject(
                    source=rasterio.band(src, bands),
                    destination=rasterio.band(dst, bands),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear,
                )

    def convert_to_cog(self, input_path: str, output_path: str):
        with rasterio.open(input_path) as dataset:
            copy(dataset, output_path, driver="COG", compress="deflate")


