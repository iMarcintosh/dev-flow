from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

engine = create_async_engine(settings.database_url, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Synchronous session for Celery tasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create sync engine from async URL
sync_database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
sync_engine = create_engine(sync_database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
