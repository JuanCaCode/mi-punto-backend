"""Add instagram_url y facebook_url al negocio (HU-03).

Revision ID: 0003_business_social_links
Revises: 0002_business_logo
Create Date: 2026-05-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_business_social_links"
down_revision: Union[str, None] = "0002_business_logo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "businesses",
        sa.Column("instagram_url", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "businesses",
        sa.Column("facebook_url", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("businesses", "facebook_url")
    op.drop_column("businesses", "instagram_url")
