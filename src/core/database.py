from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from src.core.config import settings


# Naming convention for database constraints (indexes, keys, etc.)
# This ensures consistency across the database schema.
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

# Create a metadata object with the defined naming convention
metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

# Define the base class for declarative models
# All our DB models will inherit from this class.
Base = declarative_base(metadata=metadata)

# Create the async engine for connecting to the database
# `echo=True` is useful for debugging as it logs all SQL statements.
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Create a configured "Session" class
# This is a factory for creating new session objects.
AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Important for async usage
)

# Dependency to get a DB session. This will be used in API routes.
async def get_db_session() -> AsyncSession:
    """
    Dependency function that yields a new SQLAlchemy async session.
    """
    async with AsyncSessionFactory() as session:
        yield session
