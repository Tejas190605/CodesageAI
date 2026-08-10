"""phase_5b_repository_intelligence

Revision ID: 005_repo_intelligence
Revises: 004_phase_5a_ai_schema
Create Date: 2026-08-05 08:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "005_repo_intelligence"
down_revision: Union[str, None] = "004_phase_5a_ai_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Attempt pgvector extension creation if using PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # repository_indexes table
    op.create_table(
        "repository_indexes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository", sa.String(length=200), nullable=False),
        sa.Column("commit_sha", sa.String(length=40), nullable=False),
        sa.Column("branch", sa.String(length=100), server_default="main", nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=True),
        sa.Column("index_version", sa.String(length=20), server_default="1.0.0", nullable=True),
        sa.Column("embedding_provider", sa.String(length=50), server_default="gemini", nullable=True),
        sa.Column("embedding_model", sa.String(length=100), server_default="text-embedding-004", nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("indexed_files", sa.Integer(), server_default="0", nullable=True),
        sa.Column("failed_files", sa.Integer(), server_default="0", nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_repository_indexes_id"), "repository_indexes", ["id"], unique=False)
    op.create_index(op.f("ix_repository_indexes_repository"), "repository_indexes", ["repository"], unique=True)
    op.create_index(op.f("ix_repository_indexes_status"), "repository_indexes", ["status"], unique=False)

    # code_chunks table
    op.create_table(
        "code_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository", sa.String(length=200), nullable=False),
        sa.Column("repository_index_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("symbol_name", sa.String(length=200), nullable=True),
        sa.Column("symbol_type", sa.String(length=50), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["repository_index_id"], ["repository_indexes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_code_chunks_id"), "code_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_code_chunks_repository"), "code_chunks", ["repository"], unique=False)
    op.create_index(op.f("ix_code_chunks_repository_index_id"), "code_chunks", ["repository_index_id"], unique=False)
    op.create_index(op.f("ix_code_chunks_file_path"), "code_chunks", ["file_path"], unique=False)
    op.create_index(op.f("ix_code_chunks_language"), "code_chunks", ["language"], unique=False)
    op.create_index(op.f("ix_code_chunks_symbol_name"), "code_chunks", ["symbol_name"], unique=False)
    op.create_index(op.f("ix_code_chunks_symbol_type"), "code_chunks", ["symbol_type"], unique=False)
    op.create_index(op.f("ix_code_chunks_content_hash"), "code_chunks", ["content_hash"], unique=False)


def downgrade() -> None:
    op.drop_table("code_chunks")
    op.drop_table("repository_indexes")
