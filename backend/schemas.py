import uuid
from pydantic import BaseModel


class FileRecordResponse(BaseModel):
    id: uuid.UUID
    name: str
    bounding_box_left: float
    bounding_box_bottom: float
    bounding_box_right: float
    bounding_box_top: float
    crs: str

    model_config = {"from_attributes": True}
