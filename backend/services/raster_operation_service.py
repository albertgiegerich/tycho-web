from backend.schemas import ContrastEnhancementId
from backend.schemas import ContrastEnhancement
import numpy as np
import numpy.typing as npt

from backend.schemas import RasterOperation, RasterOperationId
from backend.services.raster_operator import RasterOperator


def get_raster_operation_service():
    return RasterOperationService(RasterOperator())


class RasterOperationService:
    def __init__(self, raster_operator: RasterOperator):
        self.raster_operator = raster_operator

    def apply_contrast_enhancement(
        self, arr: npt.NDArray[np.float64], contrast_enhancement: ContrastEnhancement
    ) -> npt.NDArray[np.float64]:
        match contrast_enhancement.id:

            case ContrastEnhancementId.TRUE_COLOR:
                return self.raster_operator.true_color(arr)

            case ContrastEnhancementId.LINEAR_STRETCH:
                return self.raster_operator.linear_stretch(arr)

            case ContrastEnhancementId.EQUALIZE_HISTOGRAM:
                return self.raster_operator.histogram_equalize(arr)

    def apply_operations(
        self,
        raster_image: npt.NDArray[np.float64],
        operations: list[RasterOperation],
    ) -> npt.NDArray[np.float64]:

        for operation in operations:
            raster_image = self._apply_operation(operation, raster_image)

        return raster_image

    def _apply_operation(
        self, operation: RasterOperation, arr: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        match operation.id:
            case RasterOperationId.DENSITY_SLICE:
                return self.raster_operator.density_slice(
                    arr, np.array(operation.breaks)
                )
            case RasterOperationId.BLUR:
                return self.raster_operator.blur(arr, operation.kernel_size)
