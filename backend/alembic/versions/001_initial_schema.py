"""Initial schema — 6 core tables.

Revision ID: 001
Revises: None
Create Date: 2026-03-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the 6 core AgentProbe tables."""
    op.create_table(
        "runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("model_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="running"),
        sa.Column("final_answer", sa.Text(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("succeeded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "steps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.String(),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=True),
        sa.Column("tool_args", sa.Text(), nullable=True),
        sa.Column("failure_type", sa.String(), nullable=False, server_default="none"),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.Float(), nullable=False),
    )

    op.create_table(
        "failures",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.String(),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "step_id",
            sa.Integer(),
            sa.ForeignKey("steps.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("failure_type", sa.String(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
    )

    op.create_table(
        "benchmark_cases",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("expected_tools", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "benchmark_suites",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("model_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_steps", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("failure_summary", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "benchmark_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "suite_id",
            sa.String(),
            sa.ForeignKey("benchmark_suites.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            sa.String(),
            sa.ForeignKey("benchmark_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            sa.String(),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("answer_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tools_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("failures", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    """Drop all core tables."""
    op.drop_table("benchmark_results")
    op.drop_table("benchmark_suites")
    op.drop_table("benchmark_cases")
    op.drop_table("failures")
    op.drop_table("steps")
    op.drop_table("runs")
