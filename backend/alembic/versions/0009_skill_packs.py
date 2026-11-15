"""Versioned cybersecurity skill packs and releases.

Revision ID: 0009_skills
Revises: 0008_agentic
Create Date: 2026-11-07
"""
import sqlalchemy as sa
from alembic import op

revision = "0009_skills"
down_revision = "0008_agentic"
branch_labels = None
depends_on = None


def _tables(inspector) -> set[str]:
    return set(inspector.get_table_names())


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = _tables(inspector)
    if "skill_packs" not in existing:
        op.create_table(
            "skill_packs",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("key", sa.String(128), nullable=False, index=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("category", sa.String(64), nullable=False, server_default="wstg"),
            sa.Column("source", sa.String(256), nullable=False, server_default=""),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("skills", sa.JSON(), nullable=True),
            sa.Column("integrity_hash", sa.String(128), nullable=False, server_default=""),
            sa.Column("state", sa.String(32), nullable=False, server_default="DRAFT"),
            sa.Column("author_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("change_reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "skill_releases" not in existing:
        op.create_table(
            "skill_releases",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("manifest", sa.JSON(), nullable=True),
            sa.Column("state", sa.String(32), nullable=False, server_default="DRAFT"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("validated", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("activated_by", sa.String(64), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = _tables(inspector)
    if "skill_releases" in existing:
        op.drop_table("skill_releases")
    if "skill_packs" in existing:
        op.drop_table("skill_packs")
