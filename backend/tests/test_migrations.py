import pytest
from alembic.config import Config
from alembic import command
from app.config import settings


def test_alembic_migrations():
    """Verifies that Alembic upgrade and downgrade commands run cleanly."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///:memory:")

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Re-upgrade to head
    command.upgrade(alembic_cfg, "head")
