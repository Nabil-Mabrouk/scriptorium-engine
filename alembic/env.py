import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# --- Add project root to Python path ---
# This allows Alembic to import from our 'src' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import Base
from src.project.models import * # Import all models here
from src.crew.models import * 
# --- Load .env file ---
# This ensures the DATABASE_URL is available for Alembic
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get the async URL from the environment
db_url = os.environ['DATABASE_URL']
# If using the async driver, replace it with a sync one for Alembic
# Correctly rewrite the async SQLite URL to its standard sync form
if db_url.startswith("sqlite+aiosqlite"):
    db_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///") # <<< CORRECTED LINE
elif db_url.startswith("postgresql+psycopg"):
    db_url = db_url.replace("postgresql+psycopg", "postgresql+psycopg2")

config.set_main_option('sqlalchemy.url', db_url)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()