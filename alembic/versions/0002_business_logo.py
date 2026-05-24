"""Add logo_path column to businesses (HU-01).

Revision ID: 0002_business_logo
Revises: 0001_initial_schema
Create Date: 2026-05-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_business_logo"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "businesses",
        sa.Column("logo_path", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("businesses", "logo_path")
