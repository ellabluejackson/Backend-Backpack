# Run from Backend-Backpack: pytest -q

import uuid

from fastapi.testclient import TestClient

from files.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_folders_requires_auth():
    r = client.get("/folders")
    assert r.status_code == 401


def test_signup_then_folders_scoped():
    email = f"u_{uuid.uuid4().hex[:12]}@example.com"
    r = client.post(
        "/auth/signup",
        json={"name": "Test User", "email": email, "password": "secret1"},
    )
    assert r.status_code == 200
    data = r.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/folders", headers=headers)
    assert r.status_code == 200
    assert r.json() == []

    r = client.post("/folders", headers=headers, json={"name": "Math"})
    assert r.status_code == 200
    folder_id = r.json()["id"]

    r = client.post(
        "/flashcards",
        headers=headers,
        json={"front": "2+2", "back": "4", "folder_id": folder_id},
    )
    assert r.status_code == 200

    r = client.get("/flashcards", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
