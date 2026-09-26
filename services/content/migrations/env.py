from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from igot_content.database import Base, SCHEMA
from igot_content import database  # noqa: F401

config = context.config
settings = __import__("igot_content.config", fromlist=["get_settings"]).get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True, include_schemas=True, version_table_schema=SCHEMA)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_schemas=True, version_table_schema=SCHEMA)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
