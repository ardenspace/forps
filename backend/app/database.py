import ssl

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# postgresql:// → postgresql+asyncpg://
def get_async_url(url: str) -> str:
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


def get_connect_args(url: str) -> dict:
    """로컬호스트/내부 네트워크는 SSL skip, 외부 DB(Supabase 등)는 SSL 필요.

    URL 에 `ssl=disable` 명시 시 (예: docker compose internal network) 강제 plaintext.
    pooler self-signed 인증서 허용을 위해 외부 SSL 은 verify 끔.
    """
    if "ssl=disable" in url:
        return {}
    if "localhost" not in url and "127.0.0.1" not in url:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return {"ssl": ctx}
    return {}


engine = create_async_engine(
    get_async_url(settings.database_url),
    connect_args=get_connect_args(settings.database_url),
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
