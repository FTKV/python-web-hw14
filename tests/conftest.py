from datetime import date
from unittest.mock import MagicMock

from fastapi_limiter import FastAPILimiter
from httpx import AsyncClient
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)

from src.database.models import User

from main import app
from src.conf.config import settings
from src.database.models import Base, User
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
    session = AsyncDBSession()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="module")
async def client(session):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session():
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_session] = override_get_session
    await FastAPILimiter.init(redis_db0)
    yield AsyncClient(
        app=app,
        base_url=f"{settings.api_protocol}://{settings.api_host}:{settings.api_port}",
    )


@pytest.fixture(scope="function")
async def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email_for_verification", mock_send_email)
    await client.post("/api/auth/signup", json=user)
    stmt = select(User).filter(User.email == user.get("email"))
    current_user = await session.execute(stmt)
    current_user = current_user.scalar()
    current_user.is_email_confirmed = True
    await session.commit()
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    data = response.json()
    return data["access_token"]


@pytest.fixture(scope="session")
def user():
    return {
        "username": "test",
        "email": "test@test.com",
        "password": "1234567890",
    }


@pytest.fixture(scope="session")
def contact_to_create():
    return {
        "first_name": "test",
        "last_name": "test",
        "email": "test@test.com",
        "phone": "1234567890",
        "birthday": str(date.today()),
        "address": "test",
    }


@pytest.fixture(scope="session")
def contact_to_update():
    return {
        "first_name": "new_test",
        "last_name": "new_test",
        "email": "new_test@test.com",
        "phone": "0987654321",
        "birthday": str(date.today()),
        "address": "new_test",
    }
