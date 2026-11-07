"""MCP authority, registry, and scan job hardening.

Revision ID: 0006_mcp_hard
Revises: 0005_mcp_idem
Create Date: 2026-11-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0006_mcp_hard"
down_revision = "0005_mcp_idem"
branch_labels = None
depends_on = None

COLUMNS = {
    "mcp_servers": {
        "revoked_at": sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        "revoked_reason": sa.Column("revoked_reason", sa.Text(), nullable=False, server_default=""),
    },
    "mcp_tool_manifests": {
        "validation_detail": sa.Column("validation_detail", sa.JSON(), nullable=True),
        "validated_at": sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        "validated_by": sa.Column("validated_by", sa.String(64), nullable=False, server_default=""),
    },
    "mcp_execution_authorities": {
        "manifest_id": sa.Column("manifest_id", sa.String(64), nullable=False, server_default=""),
        "manifest_hash": sa.Column("manifest_hash", sa.String(128), nullable=False, server_default=""),
        "tool_version": sa.Column("tool_version", sa.String(64), nullable=False, server_default=""),
        "consumed_at": sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        "checkpoint_at": sa.Column("checkpoint_at", sa.DateTime(timezone=True), nullable=True),
        "revoked_at": sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    },
    "mcp_invocations": {
        "tool_version": sa.Column("tool_version", sa.String(64), nullable=False, server_default=""),
        "protocol_revision": sa.Column("protocol_revision", sa.String(64), nullable=False, server_default=""),
        "server_version": sa.Column("server_version", sa.String(64), nullable=False, server_default=""),
        "manifest_hash": sa.Column("manifest_hash", sa.String(128), nullable=False, server_default=""),
        "correlation_id": sa.Column("correlation_id", sa.String(128), nullable=False, server_default=""),
        "outcome_detail": sa.Column("outcome_detail", sa.JSON(), nullable=True),
    },
    "mcp_scan_jobs": {
        "authority_token": sa.Column("authority_token", sa.Text(), nullable=False, server_default=""),
        "lease_id": sa.Column("lease_id", sa.String(64), nullable=False, server_default=""),
        "cancel_requested_at": sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
        "cancelled_at": sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        "heartbeat_at": sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        "error": sa.Column("error", sa.Text(), nullable=False, server_default=""),
        "evidence_refs": sa.Column("evidence_refs", sa.JSON(), nullable=True),
    },
}


def _columns(inspector, table):
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    for table, columns in COLUMNS.items():
        inspector = sa.inspect(op.get_bind())
        existing = _columns(inspector, table)
        for name, column in columns.items():
            if name not in existing:
                op.add_column(table, column)


def downgrade() -> None:
    for table, columns in COLUMNS.items():
        inspector = sa.inspect(op.get_bind())
        existing = _columns(inspector, table)
        with op.batch_alter_table(table) as batch:
            for name in columns:
                if name in existing:
                    batch.drop_column(name)
