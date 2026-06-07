"""Une las dos cabezas de migracion (avatar de usuario y redes sociales).

Las HU se desarrollaron en ramas paralelas y cada una genero su propia
migracion a partir de 0001, dejando dos heads:
  - 0002_user_avatar
  - 0003_business_social_links

Esta migracion de merge las reconcilia en una sola cabeza. No modifica el
esquema; solo une el historial.

Revision ID: 0004_merge_heads
Revises: 0002_user_avatar, 0003_business_social_links
Create Date: 2026-06-07

"""
from typing import Sequence, Union

revision: str = "0004_merge_heads"
down_revision: Union[str, Sequence[str], None] = (
    "0002_user_avatar",
    "0003_business_social_links",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
