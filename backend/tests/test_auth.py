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


def _login(client) -> dict:
    client.post("/api/auth/register", json=FAKE_USER)
    creds = {"username": FAKE_USER["username"], "password": FAKE_USER["password"]}
    resp = client.post("/api/auth/login", json=creds)
    assert resp.status_code == 200
    return resp.json()


def test_login_returns_refresh_token(client):
    body = _login(client)
    assert len(body["refresh_token"]) > 20
    assert body["token_type"] == "bearer"


def test_refresh_rotates_and_old_token_invalid(client):
    old = _login(client)["refresh_token"]

    resp = client.post("/api/auth/refresh", json={"refresh_token": old})
    assert resp.status_code == 200
    rotated = resp.json()
    assert rotated["refresh_token"] != old
    assert rotated["user"]["username"] == FAKE_USER["username"]

    # 旋转后旧 refresh token 立即作废
    resp = client.post("/api/auth/refresh", json={"refresh_token": old})
    assert resp.status_code == 401

    # 新 token 仍可继续刷新
    resp = client.post("/api/auth/refresh", json={"refresh_token": rotated["refresh_token"]})
    assert resp.status_code == 200


def test_refresh_rejects_unknown_token(client):
    resp = client.post("/api/auth/refresh", json={"refresh_token": "not-a-real-token-value"})
    assert resp.status_code == 401


def test_logout_revokes_refresh_token(client):
    body = _login(client)
    resp = client.post("/api/auth/logout", json={"refresh_token": body["refresh_token"]})
    assert resp.status_code == 204

    resp = client.post("/api/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert resp.status_code == 401


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
