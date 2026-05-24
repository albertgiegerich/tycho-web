from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import URL
from backend.config import settings

APP_DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.db_user_app,
    password=settings.db_password_app,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

engine = create_async_engine(APP_DATABASE_URL)


async def get_session():
    async with AsyncSession(engine) as session:
        yield session
