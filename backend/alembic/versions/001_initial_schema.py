"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-04 22:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Repositories Table
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("default_branch", sa.String(length=100), nullable=True),
        sa.Column("private", sa.Boolean(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_repositories_id"), "repositories", ["id"], unique=False)
    op.create_index(op.f("ix_repositories_owner"), "repositories", ["owner"], unique=False)
    op.create_index(op.f("ix_repositories_name"), "repositories", ["name"], unique=False)
    op.create_index(op.f("ix_repositories_full_name"), "repositories", ["full_name"], unique=True)

    # 2. Pull Requests Table
    op.create_table(
        "pull_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("github_pr_id", sa.Integer(), nullable=True),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=True),
        sa.Column("author", sa.String(length=100), nullable=True),
        sa.Column("additions", sa.Integer(), nullable=True),
        sa.Column("deletions", sa.Integer(), nullable=True),
        sa.Column("changed_files", sa.Integer(), nullable=True),
        sa.Column("commits", sa.Integer(), nullable=True),
        sa.Column("html_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_pull_requests_id"), "pull_requests", ["id"], unique=False)
    op.create_index(op.f("ix_pull_requests_github_pr_id"), "pull_requests", ["github_pr_id"], unique=False)
    op.create_index(op.f("ix_pull_requests_number"), "pull_requests", ["number"], unique=False)
    op.create_index(op.f("ix_pull_requests_state"), "pull_requests", ["state"], unique=False)

    # 3. Reviews Table
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pull_request_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("overall_rating", sa.Integer(), nullable=True),
        sa.Column("markdown", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["pull_request_id"], ["pull_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_reviews_id"), "reviews", ["id"], unique=False)

    # 4. Findings Table
    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column("file", sa.String(length=500), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("suggested_fix", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_findings_id"), "findings", ["id"], unique=False)
    op.create_index(op.f("ix_findings_category"), "findings", ["category"], unique=False)
    op.create_index(op.f("ix_findings_severity"), "findings", ["severity"], unique=False)

    # 5. Webhook Deliveries Table
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("delivery_id", sa.String(length=100), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_webhook_deliveries_id"), "webhook_deliveries", ["id"], unique=False)
    op.create_index(op.f("ix_webhook_deliveries_delivery_id"), "webhook_deliveries", ["delivery_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_webhook_deliveries_delivery_id"), table_name="webhook_deliveries")
    op.drop_index(op.f("ix_webhook_deliveries_id"), table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")

    op.drop_index(op.f("ix_findings_severity"), table_name="findings")
    op.drop_index(op.f("ix_findings_category"), table_name="findings")
    op.drop_index(op.f("ix_findings_id"), table_name="findings")
    op.drop_table("findings")

    op.drop_index(op.f("ix_reviews_id"), table_name="reviews")
    op.drop_table("reviews")

    op.drop_index(op.f("ix_pull_requests_state"), table_name="pull_requests")
    op.drop_index(op.f("ix_pull_requests_number"), table_name="pull_requests")
    op.drop_index(op.f("ix_pull_requests_github_pr_id"), table_name="pull_requests")
    op.drop_index(op.f("ix_pull_requests_id"), table_name="pull_requests")
    op.drop_table("pull_requests")

    op.drop_index(op.f("ix_repositories_full_name"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_name"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_owner"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_id"), table_name="repositories")
    op.drop_table("repositories")
