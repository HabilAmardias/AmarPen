"""Encrypted model profile API keys.

Revision ID: 0007_model_key
Revises: 0006_mcp_hard
Create Date: 2026-11-06
"""
import sqlalchemy as sa
from alembic import op

revision = "0007_model_key"
down_revision = "0006_mcp_hard"
branch_labels = None
depends_on = None


def _columns(inspector, table: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = _columns(inspector, "model_profiles")
    if "api_key_encrypted" not in existing:
        op.add_column("model_profiles", sa.Column("api_key_encrypted", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = _columns(inspector, "model_profiles")
    with op.batch_alter_table("model_profiles") as batch:
        if "api_key_encrypted" in existing:
            batch.drop_column("api_key_encrypted")
