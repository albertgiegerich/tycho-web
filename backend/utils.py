from typing import Any, Tuple, TypeVar

import numpy as np
import numpy.typing as npt


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


def min_max_scale(
    arr: npt.NDArray[ScalarT], new_min: ScalarT, new_max: ScalarT
) -> npt.NDArray[ScalarT]:
    old_min = np.min(arr)
    old_max = np.max(arr)

    return (arr - old_min) / (old_max - old_min) * (new_max - new_min) + new_min
