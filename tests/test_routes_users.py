import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from unittest.mock import MagicMock

import cloudinary
import pytest
from sqlalchemy import select

from src.database.models import User


@pytest.fixture
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


@pytest.mark.anyio
async def test_read_me(client, token):
    response = await client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "test@test.com"


@pytest.mark.anyio
async def test_update_avatar(client, token):
    avatar_url = "http://test.com/avatar"
    cloudinary.config = MagicMock()
    cloudinary.uploader.upload = MagicMock()
    cloudinary.CloudinaryImage = MagicMock()
    cloudinary.CloudinaryImage.return_value.build_url.return_value = avatar_url
    response = await client.patch(
        "/api/users/avatar",
        files={"file": __file__},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["avatar"] == avatar_url
