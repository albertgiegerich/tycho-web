from enum import Enum

import numpy as np
import numpy.typing as npt

from backend.services.radiometric_correction import RadiometricCorrector


class RasterOperationId(Enum):
    TRUE_COLOR = "true_color"


def get_raster_operation_service():
    return RasterOperationService(RadiometricCorrector())


def dtype_max(dtype: np.dtype) -> float:
    match dtype.kind:
        case "u" | "i":
            return np.iinfo(dtype).max
        case "f":
            return np.finfo(dtype).max
        case _:
            raise ValueError(f"Unsupported dtype kind: {dtype.kind}")


class RasterOperationService:
    def __init__(self, radiometric_corrector: RadiometricCorrector):
        self.radiometric_corrector = radiometric_corrector

    def apply_operations(
        self,
        raster_image: npt.NDArray[np.float64],
        operations: list[RasterOperationId],
    ) -> npt.NDArray[np.float64]:

        for operation in operations:
            raster_image = self._apply_operation(operation, raster_image)

        return raster_image

    def _apply_operation(
        self, operation: RasterOperationId, arr: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        match operation:
            case RasterOperationId.TRUE_COLOR:
                return self.radiometric_corrector.true_color(arr)
