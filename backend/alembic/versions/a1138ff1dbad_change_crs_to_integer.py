"""change crs to integer

Revision ID: a1138ff1dbad
Revises: ffa868c314b0
Create Date: 2026-05-28 15:39:52.559734

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1138ff1dbad"
down_revision: Union[str, Sequence[str], None] = "ffa868c314b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE raster SET crs = REPLACE(crs, 'EPSG:', '') WHERE crs LIKE 'EPSG:%'"
    )
    op.alter_column(
        "raster",
        "crs",
        existing_type=sa.VARCHAR(),
        type_=sa.Integer(),
        postgresql_using="crs::integer",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "raster",
        "crs",
        existing_type=sa.Integer(),
        type_=sa.VARCHAR(),
        existing_nullable=False,
    )
    op.execute("UPDATE raster SET crs = 'EPSG:' || crs")
    # ### end Alembic commands ###
