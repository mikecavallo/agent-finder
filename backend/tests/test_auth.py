from .conftest import register_and_login


def test_register_login_and_me(client):
    headers = register_and_login(client, "alex")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == "alex"
    assert "hashed_password" not in r.json()


def test_duplicate_registration_rejected(client):
    register_and_login(client, "alex")
    r = client.post(
        "/api/auth/register",
        json={"username": "alex", "email": "other@example.com", "password": "another-pass-1"},
    )
    assert r.status_code == 409


def test_wrong_password_rejected(client):
    register_and_login(client, "alex", "right-password")
    r = client.post("/api/auth/token", data={"username": "alex", "password": "wrong-password"})
    assert r.status_code == 401


def test_weak_input_rejected(client):
    r = client.post("/api/auth/register", json={"username": "a", "email": "nope", "password": "short"})
    assert r.status_code == 422


def test_protected_routes_require_token(client):
    assert client.get("/api/jobs").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401


def test_health_reports_mock_provider(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["provider"] == "mock"
