"""Add MCP invocation idempotency keys.

Revision ID: 0005_mcp_idem
Revises: 0004_mcp
Create Date: 2026-11-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0005_mcp_idem"
down_revision = "0004_mcp"
branch_labels = None
depends_on = None


def _columns(inspector, table):
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "idempotency_key" not in _columns(inspector, "mcp_invocations"):
        op.add_column("mcp_invocations", sa.Column("idempotency_key", sa.String(128), nullable=False, server_default=""))
    if "idempotency_key" not in _columns(inspector, "mcp_scan_jobs"):
        op.add_column("mcp_scan_jobs", sa.Column("idempotency_key", sa.String(128), nullable=False, server_default=""))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    with op.batch_alter_table("mcp_invocations") as batch:
        if "idempotency_key" in _columns(inspector, "mcp_invocations"):
            batch.drop_column("idempotency_key")
    with op.batch_alter_table("mcp_scan_jobs") as batch:
        if "idempotency_key" in _columns(inspector, "mcp_scan_jobs"):
            batch.drop_column("idempotency_key")
