from ast import TypeVar
from typing import Tuple
import numpy as np
import rasterio
from rasterio.io import MemoryFile
import numpy.typing as npt


def convert_geotiff_to_png(geotiff_filepath: str) -> bytes:
    with rasterio.open(geotiff_filepath) as dataset:
        bands = dataset.read([1, 2, 3])

        normalized = normalize_to_new_dtype(bands, np.uint8)

        with MemoryFile() as mem_file:
            with mem_file.open(
                driver="PNG",
                height=normalized.shape[1],
                width=normalized.shape[2],
                count=3,
                dtype=np.uint8,
            ) as dst:
                dst.write(normalized)
            return mem_file.read()


def normalize_to_new_dtype[DType: np.number](
    arr: np.ndarray,
    new_dtype: type[DType],
    old_min: float | None = None,
    old_max: float | None = None,
) -> npt.NDArray[DType]:
    arr_dtype_min, arr_dtype_max = get_dtype_min_max(arr.dtype)

    # Default to the min/max values for the array's dtype
    old_min = arr_dtype_min if old_min is None else old_min
    old_max = arr_dtype_max if old_max is None else old_max

    new_min, new_max = get_dtype_min_max(np.dtype(new_dtype))

    normalized = normalize_0_to_1(arr)
    normalized = normalized * (new_max - new_min) + new_min

    if np.dtype(new_dtype).kind in ("i", "u"):
        normalized = np.round(normalized)

    return normalized.astype(new_dtype)


def normalize_0_to_1(arr: np.ndarray) -> npt.NDArray[np.float64]:
    dtype_min, dtype_max = get_dtype_min_max(arr.dtype)

    arr = arr.astype(np.float64)
    return (arr - dtype_min) / (dtype_max - dtype_min)


def get_dtype_min_max(arr_dtype: np.dtype) -> Tuple[int, int]:
    match arr_dtype.kind:
        case "i" | "u":
            return np.iinfo(arr_dtype).min, np.iinfo(arr_dtype).max
        case "f":
            return np.finfo(arr_dtype).min, np.finfo(arr_dtype).max
        case _:
            raise ValueError(f"Unsupported dtype kind: {arr_dtype.kind}")
