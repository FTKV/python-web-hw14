import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from unittest.mock import MagicMock

import cloudinary
import pytest


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
