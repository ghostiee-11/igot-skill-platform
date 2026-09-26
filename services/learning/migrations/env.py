from alembic import context
from sqlalchemy import engine_from_config,pool
from igot_learning.adapters.database import Base,DATABASE_URL,SCHEMA
from igot_learning.domain import models  # noqa: F401
config=context.config; config.set_main_option("sqlalchemy.url",DATABASE_URL.replace("%","%%")); target_metadata=Base.metadata
def offline():
    context.configure(url=DATABASE_URL,target_metadata=target_metadata,literal_binds=True,include_schemas=True,version_table_schema=SCHEMA)
    with context.begin_transaction(): context.run_migrations()
def online():
    with engine_from_config(config.get_section(config.config_ini_section),prefix="sqlalchemy.",poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,include_schemas=True,version_table_schema=SCHEMA)
        with context.begin_transaction(): context.run_migrations()
offline() if context.is_offline_mode() else online()
