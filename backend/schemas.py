import uuid
from pydantic import BaseModel


class FileRecordResponse(BaseModel):
    id: uuid.UUID
    name: str
    bounds: tuple[float, float, float, float]
    crs: str

    model_config = {"from_attributes": True}
