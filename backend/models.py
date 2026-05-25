from sqlalchemy import Double
from sqlalchemy import Float
import uuid
from sqlalchemy.ext.asyncio.session import AsyncAttrs
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import UUID


class Base(AsyncAttrs, DeclarativeBase):
    pass


class FileRecord(Base):
    __tablename__ = "file"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    path: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    bounding_box_left: Mapped[float] = mapped_column(Double, nullable=False)
    bounding_box_bottom: Mapped[float] = mapped_column(Double, nullable=False)
    bounding_box_right: Mapped[float] = mapped_column(Double, nullable=False)
    bounding_box_top: Mapped[float] = mapped_column(Double, nullable=False)
    crs: Mapped[str] = mapped_column(String, nullable=False)
