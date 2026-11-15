"""Discovered external origins pending scope approval.

Revision ID: 0010_origins
Revises: 0009_skills
Create Date: 2026-11-07
"""
import sqlalchemy as sa
from alembic import op

revision = "0010_origins"
down_revision = "0009_skills"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "discovered_origins" in set(inspector.get_table_names()):
        return
    op.create_table(
        "discovered_origins",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("engagement_id", sa.String(64), nullable=False, index=True),
        sa.Column("run_id", sa.String(64), nullable=False, index=True),
        sa.Column("scheme", sa.String(16), nullable=False, server_default="https"),
        sa.Column("host", sa.String(256), nullable=False, index=True),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="js"),
        sa.Column("source_url", sa.String(1024), nullable=False, server_default=""),
        sa.Column("sample_paths", sa.JSON(), nullable=True),
        sa.Column("evidence_refs", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING", index=True),
        sa.Column("decision_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("decided_by", sa.String(64), nullable=False, server_default=""),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "discovered_origins" in set(inspector.get_table_names()):
        op.drop_table("discovered_origins")
