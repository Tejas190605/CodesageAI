"""phase_5a_ai_schema

Revision ID: 004_phase_5a_ai_schema
Revises: 003_phase_4c_auth_schema
Create Date: 2026-08-04 23:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "004_phase_5a_ai_schema"
down_revision: Union[str, None] = "003_phase_4c_auth_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ai_providers table
    op.create_table(
        "ai_providers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="1", nullable=True),
        sa.Column("cost_per_1k_input", sa.String(length=20), server_default="0.00015", nullable=True),
        sa.Column("cost_per_1k_output", sa.String(length=20), server_default="0.00060", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_ai_providers_id"), "ai_providers", ["id"], unique=False)
    op.create_index(op.f("ix_ai_providers_name"), "ai_providers", ["name"], unique=True)

    # prompt_templates table
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_prompt_templates_id"), "prompt_templates", ["id"], unique=False)
    op.create_index(op.f("ix_prompt_templates_name"), "prompt_templates", ["name"], unique=False)

    # ai_usage table
    op.create_table(
        "ai_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository", sa.String(length=200), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0", nullable=True),
        sa.Column("completion_tokens", sa.Integer(), server_default="0", nullable=True),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=True),
        sa.Column("estimated_cost", sa.String(length=30), server_default="0.0000", nullable=True),
        sa.Column("latency_ms", sa.Integer(), server_default="0", nullable=True),
        sa.Column("status", sa.String(length=50), server_default="success", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_ai_usage_id"), "ai_usage", ["id"], unique=False)
    op.create_index(op.f("ix_ai_usage_repository"), "ai_usage", ["repository"], unique=False)
    op.create_index(op.f("ix_ai_usage_provider"), "ai_usage", ["provider"], unique=False)

    # evaluation_runs table
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_name", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="completed", nullable=True),
        sa.Column("quality_score", sa.Integer(), server_default="95", nullable=True),
        sa.Column("total_tests", sa.Integer(), server_default="10", nullable=True),
        sa.Column("passed_tests", sa.Integer(), server_default="10", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_evaluation_runs_id"), "evaluation_runs", ["id"], unique=False)

    # evaluation_results table
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("test_case_name", sa.String(length=150), nullable=False),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("TRUE"), nullable=True),
        sa.Column("score", sa.Integer(), server_default="100", nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_evaluation_results_id"), "evaluation_results", ["id"], unique=False)

    # model_configurations table
    op.create_table(
        "model_configurations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_repo", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=50), server_default="gemini", nullable=True),
        sa.Column("model", sa.String(length=100), server_default="gemini-2.5-flash", nullable=True),
        sa.Column("temperature", sa.String(length=10), server_default="0.2", nullable=True),
        sa.Column("max_tokens", sa.Integer(), server_default="4096", nullable=True),
        sa.Column("review_depth", sa.String(length=50), server_default="thorough", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_model_configurations_id"), "model_configurations", ["id"], unique=False)
    op.create_index(op.f("ix_model_configurations_owner_repo"), "model_configurations", ["owner_repo"], unique=True)


def downgrade() -> None:
    op.drop_table("model_configurations")
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_runs")
    op.drop_table("ai_usage")
    op.drop_table("prompt_templates")
    op.drop_table("ai_providers")
