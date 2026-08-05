"""phase_5c_policy_engine

Revision ID: 006_phase_5c_policy_engine
Revises: 005_phase_5b_repository_intelligence
Create Date: 2026-08-05 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "006_phase_5c_policy_engine"
down_revision: Union[str, None] = "005_phase_5b_repository_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # review_policies table
    op.create_table(
        "review_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("repository_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("1"), nullable=True),
        sa.Column("version", sa.String(length=20), server_default="1.0.0", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_review_policies_id"), "review_policies", ["id"], unique=False)
    op.create_index(op.f("ix_review_policies_organization_id"), "review_policies", ["organization_id"], unique=False)
    op.create_index(op.f("ix_review_policies_repository_id"), "review_policies", ["repository_id"], unique=False)

    # review_rules table
    op.create_table(
        "review_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("rule_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), server_default="security", nullable=True),
        sa.Column("severity", sa.String(length=20), server_default="high", nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("1"), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["policy_id"], ["review_policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_review_rules_id"), "review_rules", ["id"], unique=False)
    op.create_index(op.f("ix_review_rules_policy_id"), "review_rules", ["policy_id"], unique=False)
    op.create_index(op.f("ix_review_rules_rule_key"), "review_rules", ["rule_key"], unique=False)
    op.create_index(op.f("ix_review_rules_category"), "review_rules", ["category"], unique=False)
    op.create_index(op.f("ix_review_rules_severity"), "review_rules", ["severity"], unique=False)

    # policy_evaluations table
    op.create_table(
        "policy_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.Integer(), nullable=True),
        sa.Column("policy_id", sa.Integer(), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("1"), nullable=True),
        sa.Column("warning_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("failure_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("blocking_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["policy_id"], ["review_policies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_policy_evaluations_id"), "policy_evaluations", ["id"], unique=False)
    op.create_index(op.f("ix_policy_evaluations_review_id"), "policy_evaluations", ["review_id"], unique=False)
    op.create_index(op.f("ix_policy_evaluations_policy_id"), "policy_evaluations", ["policy_id"], unique=False)

    # rule_evaluations table
    op.create_table(
        "rule_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("policy_evaluation_id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=True),
        sa.Column("rule_key", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pass", nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["policy_evaluation_id"], ["policy_evaluations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["review_rules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_rule_evaluations_id"), "rule_evaluations", ["id"], unique=False)
    op.create_index(op.f("ix_rule_evaluations_policy_evaluation_id"), "rule_evaluations", ["policy_evaluation_id"], unique=False)


def downgrade() -> None:
    op.drop_table("rule_evaluations")
    op.drop_table("policy_evaluations")
    op.drop_table("review_rules")
    op.drop_table("review_policies")
