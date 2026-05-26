"""rename file table to raster

Revision ID: ffa868c314b0
Revises: ee61ef0101cd
Create Date: 2026-05-25 21:47:39.252353

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ffa868c314b0"
down_revision: Union[str, Sequence[str], None] = "ee61ef0101cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("file", "raster")


def downgrade() -> None:
    op.rename_table("raster", "file")
