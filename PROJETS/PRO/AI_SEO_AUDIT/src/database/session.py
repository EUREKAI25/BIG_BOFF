"""Database session configuration."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Base for models
Base = declarative_base()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai_seo_user:ai_seo_password@localhost:5432/ai_seo_audit")

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Async engine and session
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


async def get_db() -> AsyncSession:
    """Dependency for FastAPI to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
