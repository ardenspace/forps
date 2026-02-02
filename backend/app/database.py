from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# postgresql:// → postgresql+asyncpg://
def get_async_url(url: str) -> str:
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


engine = create_async_engine(get_async_url(settings.database_url))
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
