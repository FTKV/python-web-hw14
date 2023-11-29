import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from unittest.mock import MagicMock

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
async def test_create_contact(client, contact_to_create, token):
    response = await client.post(
        "/api/contacts",
        json=contact_to_create,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == contact_to_create["first_name"]
    assert data["last_name"] == contact_to_create["last_name"]
    assert data["email"] == contact_to_create["email"]
    assert data["phone"] == contact_to_create["phone"]
    assert data["birthday"] == contact_to_create["birthday"]
    assert data["address"] == contact_to_create["address"]
    assert "id" in data


@pytest.mark.anyio
async def test_repeat_create_contact(client, contact_to_create, token):
    response = await client.post(
        "/api/contacts",
        json=contact_to_create,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "The contact's email and/or phone already exist"


@pytest.mark.anyio
async def test_read_contact(client, token, contact_to_create):
    response = await client.get(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == contact_to_create["first_name"]
    assert data["last_name"] == contact_to_create["last_name"]
    assert data["email"] == contact_to_create["email"]
    assert data["phone"] == contact_to_create["phone"]
    assert data["birthday"] == contact_to_create["birthday"]
    assert data["address"] == contact_to_create["address"]
    assert "id" in data


@pytest.mark.anyio
async def test_read_contact_not_found(client, token):
    response = await client.get(
        "/api/contacts/2", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Contact not found"


@pytest.mark.anyio
async def test_read_contacts(client, token, contact_to_create):
    response = await client.get(
        "/api/contacts", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == contact_to_create["first_name"]
    assert data[0]["last_name"] == contact_to_create["last_name"]
    assert data[0]["email"] == contact_to_create["email"]
    assert data[0]["phone"] == contact_to_create["phone"]
    assert data[0]["birthday"] == contact_to_create["birthday"]
    assert data[0]["address"] == contact_to_create["address"]
    assert "id" in data[0]


@pytest.mark.anyio
async def test_read_contacts_birthdays_in_n_days(client, token, contact_to_create):
    response = await client.get(
        "/api/contacts/birthdays_in_1_days",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == contact_to_create["first_name"]
    assert data[0]["last_name"] == contact_to_create["last_name"]
    assert data[0]["email"] == contact_to_create["email"]
    assert data[0]["phone"] == contact_to_create["phone"]
    assert data[0]["birthday"] == contact_to_create["birthday"]
    assert data[0]["address"] == contact_to_create["address"]
    assert "id" in data[0]


@pytest.mark.anyio
async def test_update_contact(client, token, contact_to_update):
    response = await client.put(
        "/api/contacts/1",
        json=contact_to_update,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == contact_to_update["first_name"]
    assert data["last_name"] == contact_to_update["last_name"]
    assert data["email"] == contact_to_update["email"]
    assert data["phone"] == contact_to_update["phone"]
    assert data["birthday"] == contact_to_update["birthday"]
    assert data["address"] == contact_to_update["address"]
    assert "id" in data


@pytest.mark.anyio
async def test_update_contact_not_found(client, token, contact_to_update):
    response = await client.put(
        "/api/contacts/2",
        json=contact_to_update,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Contact not found"


@pytest.mark.anyio
async def test_delete_contact(client, token):
    response = await client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204


@pytest.mark.anyio
async def test_repeat_delete_contact(client, token):
    response = await client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Contact not found"
