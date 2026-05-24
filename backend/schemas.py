import uuid
from pydantic import BaseModel


class FileRecordResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}
