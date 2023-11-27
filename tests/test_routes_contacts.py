import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from datetime import date
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
async def test_create_contact(client, token):
    response = await client.post(
        "/api/contacts",
        json={
            "first_name": "test",
            "last_name": "test",
            "email": "test@test.com",
            "phone": "1234567890",
            "birthday": str(date.today()),
            "address": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == "test"
    assert data["last_name"] == "test"
    assert data["email"] == "test@test.com"
    assert data["phone"] == "1234567890"
    assert data["birthday"] == str(date.today())
    assert data["address"] == "test"
    assert "id" in data


@pytest.mark.anyio
async def test_read_contact(client, token):
    response = await client.get(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "test"
    assert data["last_name"] == "test"
    assert data["email"] == "test@test.com"
    assert data["phone"] == "1234567890"
    assert data["birthday"] == str(date.today())
    assert data["address"] == "test"
    assert "id" in data


@pytest.mark.anyio
async def test_read_contact_not_found(client, token):
    response = await client.get(
        "/api/contacts/2", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


@pytest.mark.anyio
async def test_read_contacts(client, token):
    response = await client.get(
        "/api/contacts", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == "test"
    assert data[0]["last_name"] == "test"
    assert data[0]["email"] == "test@test.com"
    assert data[0]["phone"] == "1234567890"
    assert data[0]["birthday"] == str(date.today())
    assert data[0]["address"] == "test"
    assert "id" in data[0]


@pytest.mark.anyio
async def test_read_contacts_birthdays_in_n_days(client, token):
    response = await client.get(
        "/api/contacts/birthdays_in_1_days",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == "test"
    assert data[0]["last_name"] == "test"
    assert data[0]["email"] == "test@test.com"
    assert data[0]["phone"] == "1234567890"
    assert data[0]["birthday"] == str(date.today())
    assert data[0]["address"] == "test"
    assert "id" in data[0]


@pytest.mark.anyio
async def test_update_contact(client, token):
    response = await client.put(
        "/api/contacts/1",
        json={
            "first_name": "new_test",
            "last_name": "new_test",
            "email": "new_test@test.com",
            "phone": "0987654321",
            "birthday": str(date.today()),
            "address": "new_test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "new_test"
    assert data["last_name"] == "new_test"
    assert data["email"] == "new_test@test.com"
    assert data["phone"] == "0987654321"
    assert data["birthday"] == str(date.today())
    assert data["address"] == "new_test"
    assert "id" in data


@pytest.mark.anyio
async def test_update_contact_not_found(client, token):
    response = await client.put(
        "/api/contacts/2",
        json={
            "first_name": "new_test",
            "last_name": "new_test",
            "email": "new_test@test.com",
            "phone": "0987654321",
            "birthday": str(date.today()),
            "address": "new_test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


@pytest.mark.anyio
async def test_delete_contact(client, token):
    response = await client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204, response.text


@pytest.mark.anyio
async def test_repeat_delete_contact(client, token):
    response = await client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"
