"""review_jobs_schema

Revision ID: 002_review_jobs_schema
Revises: 001_initial_schema
Create Date: 2026-08-04 23:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_review_jobs_schema"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=100), nullable=False),
        sa.Column("repository", sa.String(length=200), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("pr_title", sa.String(length=255), nullable=True),
        sa.Column("delivery_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("max_retries", sa.Integer(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_review_jobs_id"), "review_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_review_jobs_job_id"), "review_jobs", ["job_id"], unique=True)
    op.create_index(op.f("ix_review_jobs_repository"), "review_jobs", ["repository"], unique=False)
    op.create_index(op.f("ix_review_jobs_pr_number"), "review_jobs", ["pr_number"], unique=False)
    op.create_index(op.f("ix_review_jobs_delivery_id"), "review_jobs", ["delivery_id"], unique=False)
    op.create_index(op.f("ix_review_jobs_status"), "review_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_review_jobs_status"), table_name="review_jobs")
    op.drop_index(op.f("ix_review_jobs_delivery_id"), table_name="review_jobs")
    op.drop_index(op.f("ix_review_jobs_pr_number"), table_name="review_jobs")
    op.drop_index(op.f("ix_review_jobs_repository"), table_name="review_jobs")
    op.drop_index(op.f("ix_review_jobs_job_id"), table_name="review_jobs")
    op.drop_index(op.f("ix_review_jobs_id"), table_name="review_jobs")
    op.drop_table("review_jobs")
