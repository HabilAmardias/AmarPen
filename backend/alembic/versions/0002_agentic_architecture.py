"""Agentic architecture tables and task context.

Revision ID: 0002_agentic
Revises: 0001_initial
Create Date: 2026-11-05
"""
import sqlalchemy as sa
from alembic import op

from pentest_platform.db.models import Base

revision = "0002_agentic"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

NEW_TABLES = [
    "agent_task_results",
    "agent_proposals",
    "asset_records",
    "resource_locks",
    "budget_ledgers",
]

TASK_COLUMNS = {
    "role": sa.Column("role", sa.String(64), nullable=False, server_default=""),
    "kind": sa.Column("kind", sa.String(32), nullable=False, server_default="test"),
    "asset": sa.Column("asset", sa.String(256), nullable=False, server_default=""),
    "ownership_key": sa.Column("ownership_key", sa.String(512), nullable=False, server_default=""),
    "dependency_ids": sa.Column("dependency_ids", sa.JSON(), nullable=True),
    "input_records": sa.Column("input_records", sa.JSON(), nullable=True),
    "attempt": sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
    "max_attempts": sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
    "deadline": sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
    "next_attempt_at": sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    "request_budget": sa.Column("request_budget", sa.Integer(), nullable=False, server_default="50"),
    "model_budget": sa.Column("model_budget", sa.Integer(), nullable=False, server_default="8"),
    "iteration_budget": sa.Column("iteration_budget", sa.Integer(), nullable=False, server_default="3"),
    "prompt_release_id": sa.Column("prompt_release_id", sa.String(64), nullable=False, server_default=""),
    "prompt_version": sa.Column("prompt_version", sa.Integer(), nullable=False, server_default="0"),
    "prompt_hash": sa.Column("prompt_hash", sa.String(128), nullable=False, server_default=""),
    "model_profile": sa.Column("model_profile", sa.String(128), nullable=False, server_default=""),
    "outcome": sa.Column("outcome", sa.String(32), nullable=False, server_default=""),
    "lease_id": sa.Column("lease_id", sa.String(64), nullable=False, server_default=""),
    "result_id": sa.Column("result_id", sa.String(64), nullable=False, server_default=""),
}

OTHER_COLUMNS = {
    "scenarios": {"agent_role": sa.Column("agent_role", sa.String(64), nullable=False, server_default="")},
    "findings": {
        "scenario_id": sa.Column("scenario_id", sa.String(64), nullable=False, server_default=""),
        "scenario_version": sa.Column("scenario_version", sa.String(32), nullable=False, server_default=""),
        "origin_task_id": sa.Column("origin_task_id", sa.String(64), nullable=False, server_default=""),
    },
    "retest_attempts": {
        "config_snapshot": sa.Column("config_snapshot", sa.JSON(), nullable=True),
    },
}


def _columns(inspector, table: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for name in NEW_TABLES:
        if name not in existing_tables:
            Base.metadata.tables[name].create(bind)

    inspector = sa.inspect(bind)
    if "tasks" in existing_tables:
        existing = _columns(inspector, "tasks")
        for name, column in TASK_COLUMNS.items():
            if name not in existing:
                op.add_column("tasks", column)
    for table, columns in OTHER_COLUMNS.items():
        if table not in existing_tables:
            continue
        existing = _columns(sa.inspect(bind), table)
        for name, column in columns.items():
            if name not in existing:
                op.add_column(table, column)

    op.create_index("ix_tasks_role", "tasks", ["role"], if_not_exists=True)
    op.create_index("ix_tasks_ownership_key", "tasks", ["ownership_key"], if_not_exists=True)
    op.create_index("ix_findings_scenario_id", "findings", ["scenario_id"], if_not_exists=True)
    op.create_index("ix_agent_proposals_status", "agent_proposals", ["status"], if_not_exists=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    for table in reversed(NEW_TABLES):
        if table in existing_tables:
            op.drop_table(table)
    if "tasks" in existing_tables:
        with op.batch_alter_table("tasks") as batch:
            for name in TASK_COLUMNS:
                if name in _columns(sa.inspect(bind), "tasks"):
                    batch.drop_column(name)
    for table, columns in OTHER_COLUMNS.items():
        if table not in existing_tables:
            continue
        with op.batch_alter_table(table) as batch:
            for name in columns:
                if name in _columns(sa.inspect(bind), table):
                    batch.drop_column(name)
