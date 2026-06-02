from enum import StrEnum

from typing import Annotated, Literal
import uuid
from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel
from backend.models import Raster


class DefaultConfigModel(BaseModel):
    model_config = {
        "from_attributes": True,
        "alias_generator": to_camel,
        "populate_by_name": True,
    }


class RasterResponse(DefaultConfigModel):
    id: uuid.UUID
    name: str
    bounds: tuple[float, float, float, float]
    band_count: int

    @staticmethod
    def from_raster(raster: Raster) -> "RasterResponse":
        return RasterResponse(
            id=raster.id,
            name=raster.name,
            band_count=raster.band_count,
            bounds=(
                raster.bounding_box_left,
                raster.bounding_box_bottom,
                raster.bounding_box_right,
                raster.bounding_box_top,
            ),
        )


class GetRasterRequest(DefaultConfigModel):
    band_order: tuple[int, int, int]
    contrast_enhancement: ContrastEnhancement | None
    operations: list[RasterOperation]


class RasterPixel(DefaultConfigModel):
    brightness_values: list[float]
    row: int
    col: int


class ContrastEnhancementId(StrEnum):
    TRUE_COLOR = "true_color"
    LINEAR_STRETCH = "linear_stretch"
    EQUALIZE_HISTOGRAM = "equalize_histogram"


class TrueColorEnhancement(DefaultConfigModel):
    id: Literal[ContrastEnhancementId.TRUE_COLOR]


class LinearStretchEnhancement(DefaultConfigModel):
    id: Literal[ContrastEnhancementId.LINEAR_STRETCH]


class EqualizeHistogramEnhancement(DefaultConfigModel):
    id: Literal[ContrastEnhancementId.EQUALIZE_HISTOGRAM]


type ContrastEnhancement = Annotated[
    TrueColorEnhancement | LinearStretchEnhancement | EqualizeHistogramEnhancement,
    Field(discriminator="id"),
]


class RasterOperationId(StrEnum):
    DENSITY_SLICE = "density_slice"


class DensitySliceOperation(DefaultConfigModel):
    id: Literal[RasterOperationId.DENSITY_SLICE]
    breaks: list[float]


type RasterOperation = Annotated[DensitySliceOperation, Field(discriminator="id")]
