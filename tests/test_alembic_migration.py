import pytest
from alembic.config import Config
from alembic import command
from config import settings


def test_alembic_upgrade_and_downgrade(tmp_path):
    # Test on a temporary sqlite database file
    db_file = tmp_path / "test_migration.db"
    sqlite_url = f"sqlite:///{db_file}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sqlite_url)

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Upgrade again
    command.upgrade(alembic_cfg, "head")

