"""add analysis range to songs

Revision ID: 20260801_0002
Revises: 20260718_0001
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0002"
down_revision: str | None = "20260718_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("songs", sa.Column("analysis_start_seconds", sa.Float(), nullable=True))
    op.add_column("songs", sa.Column("analysis_end_seconds", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("songs", "analysis_end_seconds")
    op.drop_column("songs", "analysis_start_seconds")
