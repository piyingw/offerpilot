FAKE_USER = {"username": "pilot", "email": "pilot@example.com", "password": "super-secret-1"}


def test_register_success(client):
    resp = client.post("/api/auth/register", json=FAKE_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == FAKE_USER["username"]
    assert body["email"] == FAKE_USER["email"]
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_rejected(client):
    client.post("/api/auth/register", json=FAKE_USER)
    resp = client.post("/api/auth/register", json=FAKE_USER)
    assert resp.status_code == 409


def test_register_validation_rejected(client):
    payload = {"username": "ab", "email": "bad", "password": "123"}
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 422


def test_login_and_me(client):
    client.post("/api/auth/register", json=FAKE_USER)

    creds = {"username": FAKE_USER["username"], "password": FAKE_USER["password"]}
    resp = client.post("/api/auth/login", json=creds)
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == FAKE_USER["username"]


def test_login_with_email(client):
    client.post("/api/auth/register", json=FAKE_USER)
    creds = {"username": FAKE_USER["email"], "password": FAKE_USER["password"]}
    resp = client.post("/api/auth/login", json=creds)
    assert resp.status_code == 200


def test_login_wrong_password(client):
    client.post("/api/auth/register", json=FAKE_USER)
    creds = {"username": FAKE_USER["username"], "password": "wrong-pass-123"}
    resp = client.post("/api/auth/login", json=creds)
    assert resp.status_code == 401


def test_me_without_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
