"""Alembic environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    cmd_opts = context.get_x_argument(as_dictionary=True)
    if "sqlalchemy.url" in cmd_opts:
        return cmd_opts["sqlalchemy.url"]
    return config.get_main_option("sqlalchemy.url", "")


def run_migrations_offline() -> None:
    context.configure(url=get_url(), target_metadata=None, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url())
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
