from logging.config import fileConfig
from alembic import context
from database.database import engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    context.configure(
        dialect_name=engine.dialect.name,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(connection=connection)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()