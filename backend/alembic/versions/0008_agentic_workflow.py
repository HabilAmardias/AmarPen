"""Authorization attestation, endpoint metadata, identities, and exchanges.

Revision ID: 0008_agentic
Revises: 0007_model_key
Create Date: 2026-11-07
"""
import sqlalchemy as sa
from alembic import op

revision = "0008_agentic"
down_revision = "0007_model_key"
branch_labels = None
depends_on = None


def _columns(inspector, table: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table)}


def _tables(inspector) -> set[str]:
    return set(inspector.get_table_names())


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    engagement_columns = _columns(inspector, "engagements")
    if "base_url" not in engagement_columns:
        op.add_column("engagements", sa.Column("base_url", sa.String(512), nullable=False, server_default=""))
    task_columns = _columns(inspector, "tasks")
    if "method" not in task_columns:
        op.add_column("tasks", sa.Column("method", sa.String(16), nullable=False, server_default="GET"))
    if "identity_id" not in task_columns:
        op.add_column("tasks", sa.Column("identity_id", sa.String(64), nullable=False, server_default=""))
    if "endpoint_ref" not in task_columns:
        op.add_column("tasks", sa.Column("endpoint_ref", sa.String(1024), nullable=False, server_default=""))
    asset_columns = _columns(inspector, "asset_records")
    if "metadata" not in asset_columns:
        op.add_column("asset_records", sa.Column("metadata", sa.JSON(), nullable=True))

    existing_tables = _tables(inspector)
    if "authorization_attestations" not in existing_tables:
        op.create_table(
            "authorization_attestations",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("engagement_id", sa.String(64), nullable=False, index=True),
            sa.Column("attested_by_user_id", sa.String(64), nullable=False),
            sa.Column("method", sa.String(32), nullable=False, server_default="clickwrap"),
            sa.Column("attestation_text", sa.Text(), nullable=False, server_default=""),
            sa.Column("attestation_text_hash", sa.String(128), nullable=False, server_default=""),
            sa.Column("scope_hash", sa.String(128), nullable=False, server_default=""),
            sa.Column("base_url", sa.String(512), nullable=False, server_default=""),
            sa.Column("targets", sa.JSON(), nullable=True),
            sa.Column("exclusions", sa.JSON(), nullable=True),
            sa.Column("window_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("window_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_ip", sa.String(128), nullable=False, server_default=""),
            sa.Column("user_agent", sa.String(512), nullable=False, server_default=""),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "test_identities" not in existing_tables:
        op.create_table(
            "test_identities",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("engagement_id", sa.String(64), nullable=False, index=True),
            sa.Column("label", sa.String(128), nullable=False),
            sa.Column("role", sa.String(64), nullable=False, server_default="user"),
            sa.Column("auth_type", sa.String(32), nullable=False, server_default="cookie"),
            sa.Column("origin", sa.String(32), nullable=False, server_default="self_registered"),
            sa.Column("username", sa.String(256), nullable=False, server_default=""),
            sa.Column("email", sa.String(256), nullable=False, server_default=""),
            sa.Column("credentials_enc", sa.Text(), nullable=False, server_default=""),
            sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "identity_sessions" not in existing_tables:
        op.create_table(
            "identity_sessions",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("run_id", sa.String(64), nullable=False, index=True),
            sa.Column("identity_id", sa.String(64), nullable=False, index=True),
            sa.Column("state", sa.String(32), nullable=False, server_default="ACTIVE"),
            sa.Column("headers_enc", sa.Text(), nullable=False, server_default=""),
            sa.Column("cookies_enc", sa.Text(), nullable=False, server_default=""),
            sa.Column("csrf_token_enc", sa.Text(), nullable=False, server_default=""),
            sa.Column("failure_reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "http_exchanges" not in existing_tables:
        op.create_table(
            "http_exchanges",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("run_id", sa.String(64), nullable=False, index=True),
            sa.Column("task_id", sa.String(64), nullable=False, index=True),
            sa.Column("identity_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("method", sa.String(16), nullable=False, server_default="GET"),
            sa.Column("url", sa.String(1024), nullable=False),
            sa.Column("status_code", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("response_headers", sa.JSON(), nullable=True),
            sa.Column("response_body_hash", sa.String(128), nullable=False, server_default=""),
            sa.Column("response_bytes", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("outcome", sa.String(32), nullable=False, server_default="COMPLETED"),
            sa.Column("evidence_ref", sa.String(1024), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "access_observations" not in existing_tables:
        op.create_table(
            "access_observations",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("run_id", sa.String(64), nullable=False, index=True),
            sa.Column("endpoint", sa.String(1024), nullable=False),
            sa.Column("method", sa.String(16), nullable=False, server_default="GET"),
            sa.Column("scenario_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("baseline_identity_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("comparison_identity_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("baseline_status", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("comparison_status", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("access_granted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("evidence_refs", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = _tables(inspector)
    for table in ("access_observations", "http_exchanges", "identity_sessions", "test_identities", "authorization_attestations"):
        if table in existing_tables:
            op.drop_table(table)
    inspector = sa.inspect(op.get_bind())
    asset_columns = _columns(inspector, "asset_records")
    with op.batch_alter_table("asset_records") as batch:
        if "metadata" in asset_columns:
            batch.drop_column("metadata")
    task_columns = _columns(inspector, "tasks")
    with op.batch_alter_table("tasks") as batch:
        for name in ("method", "identity_id", "endpoint_ref"):
            if name in task_columns:
                batch.drop_column(name)
    engagement_columns = _columns(inspector, "engagements")
    with op.batch_alter_table("engagements") as batch:
        if "base_url" in engagement_columns:
            batch.drop_column("base_url")
