"""Model profile connection test fields.

Revision ID: 0003_model_health
Revises: 0002_agentic
Create Date: 2026-11-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_model_health"
down_revision = "0002_agentic"
branch_labels = None
depends_on = None


def _columns(inspector, table: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = _columns(inspector, "model_profiles")
    if "last_tested_at" not in existing:
        op.add_column("model_profiles", sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True))
    if "last_test_status" not in existing:
        op.add_column("model_profiles", sa.Column("last_test_status", sa.String(32), nullable=False, server_default=""))
    if "last_test_detail" not in existing:
        op.add_column("model_profiles", sa.Column("last_test_detail", sa.JSON(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = _columns(inspector, "model_profiles")
    with op.batch_alter_table("model_profiles") as batch:
        for name in ("last_tested_at", "last_test_status", "last_test_detail"):
            if name in existing:
                batch.drop_column(name)
