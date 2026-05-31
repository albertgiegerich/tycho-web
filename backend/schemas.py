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
    operations: list[RasterOperation]


class RasterPixel(DefaultConfigModel):
    brightness_values: list[float]
    row: int
    col: int


class RasterOperationId(StrEnum):
    TRUE_COLOR = "true_color"
    DENSITY_SLICE = "density_slice"


class TrueColorOperation(DefaultConfigModel):
    id: Literal[RasterOperationId.TRUE_COLOR]


class DensitySliceOperation(DefaultConfigModel):
    id: Literal[RasterOperationId.DENSITY_SLICE]
    breaks: list[float]


type RasterOperation = Annotated[
    TrueColorOperation | DensitySliceOperation, Field(discriminator="id")
]
