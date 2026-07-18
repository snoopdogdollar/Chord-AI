"""initial mvp schema

Revision ID: 20260718_0001
Revises:
Create Date: 2026-07-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260718_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "songs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("original_path", sa.Text(), nullable=True),
        sa.Column("processed_path", sa.Text(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("bpm", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("song_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_processing_jobs_song_id"), "processing_jobs", ["song_id"], unique=False)
    op.create_table(
        "chord_progressions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("song_id", sa.String(), nullable=False),
        sa.Column("timestamp_start", sa.Float(), nullable=False),
        sa.Column("timestamp_end", sa.Float(), nullable=False),
        sa.Column("chord_name", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chord_progressions_song_id"), "chord_progressions", ["song_id"], unique=False)
    op.create_table(
        "generated_sheets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("song_id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generated_sheets_song_id"), "generated_sheets", ["song_id"], unique=False)
    op.create_table(
        "generated_exports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("song_id", sa.String(), nullable=False),
        sa.Column("export_format", sa.String(length=8), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generated_exports_song_id"), "generated_exports", ["song_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_generated_exports_song_id"), table_name="generated_exports")
    op.drop_table("generated_exports")
    op.drop_index(op.f("ix_generated_sheets_song_id"), table_name="generated_sheets")
    op.drop_table("generated_sheets")
    op.drop_index(op.f("ix_chord_progressions_song_id"), table_name="chord_progressions")
    op.drop_table("chord_progressions")
    op.drop_index(op.f("ix_processing_jobs_song_id"), table_name="processing_jobs")
    op.drop_table("processing_jobs")
    op.drop_table("songs")
