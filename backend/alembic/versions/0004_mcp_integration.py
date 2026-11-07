"""MCP registry, authority, invocation, and scan job records.

Revision ID: 0004_mcp
Revises: 0003_model_health
Create Date: 2026-11-05
"""
import sqlalchemy as sa
from alembic import op

from pentest_platform.db.models import Base

revision = "0004_mcp"
down_revision = "0003_model_health"
branch_labels = None
depends_on = None

TABLES = [
    "mcp_servers",
    "mcp_tool_manifests",
    "mcp_execution_authorities",
    "mcp_invocations",
    "mcp_scan_jobs",
]


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    for name in TABLES:
        if name not in existing:
            Base.metadata.tables[name].create(bind)


def downgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    for name in reversed(TABLES):
        if name in existing:
            op.drop_table(name)
