from typing import Any, Tuple, TypeVar

import numpy as np
import numpy.typing as npt

SENTINEL_NO_DATA = 0


def get_dtype_min_max(arr_dtype: np.dtype) -> Tuple[int, int]:
    match arr_dtype.kind:
        case "i" | "u":
            return np.iinfo(arr_dtype).min, np.iinfo(arr_dtype).max
        case "f":
            return np.finfo(arr_dtype).min, np.finfo(arr_dtype).max
        case _:
            raise ValueError(f"Unsupported dtype kind: {arr_dtype.kind}")


def normalize_0_to_1(arr: np.ndarray) -> npt.NDArray[np.float64]:
    _, dtype_max = get_dtype_min_max(arr.dtype)

    arr = arr.astype(np.float64)
    return arr / dtype_max


ScalarT = TypeVar("ScalarT", bound=np.number[Any])


def percentile_min_max_scale(
    arr: npt.NDArray[ScalarT],
    new_min: ScalarT,
    new_max: ScalarT,
    bottom_percentile: float = 2,
    top_percentile: float = 98,
) -> npt.NDArray[ScalarT]:

    masked = np.ma.masked_equal(arr, SENTINEL_NO_DATA)

    # Filter out some of the top and bottom values to account for outliers (specular reflection, etc.)
    old_min = np.percentile(masked.compressed(), bottom_percentile)

    # compressed returns a flat array of all the unmasked values
    old_max = np.percentile(masked.compressed(), top_percentile)

    result = (masked - old_min) / (old_max - old_min) * (new_max - new_min) + new_min
    result = np.clip(result, new_min, new_max)  # clamp outliers back into range
    return np.ma.filled(result, SENTINEL_NO_DATA)
