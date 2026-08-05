"""phase_4c_auth_schema

Revision ID: 003_phase_4c_auth_schema
Revises: 002_review_jobs_schema
Create Date: 2026-08-04 23:33:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "003_phase_4c_auth_schema"
down_revision: Union[str, None] = "002_review_jobs_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("github_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("role", sa.String(length=50), server_default="member", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_github_id"), "users", ["github_id"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("github_id", sa.Integer(), nullable=False),
        sa.Column("login", sa.String(length=100), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_organizations_id"), "organizations", ["id"], unique=False)
    op.create_index(op.f("ix_organizations_github_id"), "organizations", ["github_id"], unique=True)
    op.create_index(op.f("ix_organizations_login"), "organizations", ["login"], unique=True)

    # Org Memberships table
    op.create_table(
        "org_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), server_default="member", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_org_memberships_id"), "org_memberships", ["id"], unique=False)

    # Installations table
    op.create_table(
        "installations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("installation_id", sa.Integer(), nullable=False),
        sa.Column("account_login", sa.String(length=100), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("account_type", sa.String(length=50), server_default="User", nullable=True),
        sa.Column("target_type", sa.String(length=50), server_default="User", nullable=True),
        sa.Column("repository_selection", sa.String(length=50), server_default="all", nullable=True),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_installations_id"), "installations", ["id"], unique=False)
    op.create_index(op.f("ix_installations_installation_id"), "installations", ["installation_id"], unique=True)
    op.create_index(op.f("ix_installations_account_login"), "installations", ["account_login"], unique=False)

    # Add installation_id column to repositories table
    with op.batch_alter_table("repositories") as batch_op:
        batch_op.add_column(sa.Column("installation_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_repos_installation", "installations", ["installation_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("repositories") as batch_op:
        batch_op.drop_constraint("fk_repos_installation", type_="foreignkey")
        batch_op.drop_column("installation_id")

    op.drop_table("installations")
    op.drop_table("org_memberships")
    op.drop_table("organizations")
    op.drop_table("users")
