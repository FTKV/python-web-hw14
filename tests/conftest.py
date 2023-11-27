from httpx import AsyncClient
from fastapi_limiter import FastAPILimiter
import pytest
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)

from main import app
from src.conf.config import settings
from src.database.models import Base
from src.database.connect_db import get_session, redis_db0


SQLALCHEMY_DATABASE_URL_ASYNC = "sqlite+aiosqlite:///:memory:"

engine: AsyncEngine = create_async_engine(
    SQLALCHEMY_DATABASE_URL_ASYNC,
    echo=False,
)

AsyncDBSession = async_sessionmaker(
    engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session = AsyncDBSession()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="session")
async def client(session):
    async def override_get_session():
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_session] = override_get_session

    await FastAPILimiter.init(redis_db0)

    yield AsyncClient(
        app=app, base_url=f"http://{settings.api_host}:{settings.api_port}"
    )


@pytest.fixture(scope="session")
def user():
    return {
        "username": "test",
        "email": "test@test.com",
        "password": "1234567890",
    }
