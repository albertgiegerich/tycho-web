from enum import Enum

from typing import Annotated, Literal
import uuid
from pydantic import BaseModel, Field
from backend.models import Raster


class RasterResponse(BaseModel):
    id: uuid.UUID
    name: str
    bounds: tuple[float, float, float, float]

    model_config = {"from_attributes": True}

    @staticmethod
    def from_raster(raster: Raster) -> "RasterResponse":
        return RasterResponse(
            id=raster.id,
            name=raster.name,
            bounds=(
                raster.bounding_box_left,
                raster.bounding_box_bottom,
                raster.bounding_box_right,
                raster.bounding_box_top,
            ),
        )


class RasterPixel(BaseModel):
    brightness_values: list[float]
    row: int
    col: int


class RasterOperationId(Enum):
    TRUE_COLOR = "true_color"
    DENSITY_SLICE = "density_slice"


class TrueColorOperation(BaseModel):
    id: Literal[RasterOperationId.TRUE_COLOR]


class DensitySliceOperation(BaseModel):
    id: Literal[RasterOperationId.DENSITY_SLICE]
    breaks: list[float]


type RasterOperation = Annotated[
    TrueColorOperation | DensitySliceOperation, Field(discriminator="id")
]
