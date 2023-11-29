import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from unittest.mock import MagicMock

import pytest

from src.repository import users as repository_users


@pytest.mark.anyio
async def test_signup_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email_for_verification", mock_send_email)
    response = await client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["username"] == user.get("username")
    assert data["user"]["email"] == user.get("email")
    assert "id" in data["user"]


@pytest.mark.anyio
async def test_repeat_signup_user(client, user):
    response = await client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "The account already exists"


@pytest.mark.anyio
async def test_login_user_is_not_confirmed(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "The email is not confirmed"


@pytest.mark.anyio
async def test_login_user(client, session, user):
    current_user = await repository_users.get_user_by_email(user.get("email"), session)
    current_user.is_email_confirmed = True
    await session.commit()
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_wrong_email(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": "email", "password": user.get("password")},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email"


@pytest.mark.anyio
async def test_login_wrong_password(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": "password"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid password"
