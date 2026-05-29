from typing import Tuple
import numpy as np
import rasterio
import numpy.typing as npt
from rasterio.enums import Resampling
from rasterio.shutil import copy
from rasterio.warp import calculate_default_transform, reproject


def get_geotiff_service() -> GeoTiffService:
    return GeoTiffService()


class GeoTiffService:
    def convert_geotiff_to_png(
        self, geotiff_file_path: str, png_file_path: str
    ) -> None:
        with rasterio.open(geotiff_file_path) as dataset:
            bands = dataset.read([1, 2, 3])

            normalized = self.normalize_to_new_dtype(bands, np.uint8)

            with rasterio.open(
                png_file_path,
                mode="w",
                driver="PNG",
                height=normalized.shape[1],
                width=normalized.shape[2],
                count=3,
                dtype=np.uint8,
            ) as png_dataset:
                png_dataset.write(normalized)

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

    def normalize_to_new_dtype[DType: np.number](
        self,
        arr: np.ndarray,
        new_dtype: type[DType],
        old_min: float | None = None,
        old_max: float | None = None,
    ) -> npt.NDArray[DType]:
        arr_dtype_min, arr_dtype_max = self.get_dtype_min_max(arr.dtype)

        # Default to the min/max values for the array's dtype
        old_min = arr_dtype_min if old_min is None else old_min
        old_max = arr_dtype_max if old_max is None else old_max

        new_min, new_max = self.get_dtype_min_max(np.dtype(new_dtype))

        normalized = self.normalize_0_to_1(arr)
        normalized = normalized * (new_max - new_min) + new_min

        if np.dtype(new_dtype).kind in ("i", "u"):
            normalized = np.round(normalized)

        return normalized.astype(new_dtype)

    def normalize_0_to_1(self, arr: np.ndarray) -> npt.NDArray[np.float64]:
        dtype_min, dtype_max = self.get_dtype_min_max(arr.dtype)

        arr = arr.astype(np.float64)
        return (arr - dtype_min) / (dtype_max - dtype_min)

    def get_dtype_min_max(self, arr_dtype: np.dtype) -> Tuple[int, int]:
        match arr_dtype.kind:
            case "i" | "u":
                return np.iinfo(arr_dtype).min, np.iinfo(arr_dtype).max
            case "f":
                return np.finfo(arr_dtype).min, np.finfo(arr_dtype).max
            case _:
                raise ValueError(f"Unsupported dtype kind: {arr_dtype.kind}")
