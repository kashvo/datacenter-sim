import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limiter import reset_attempts

client = TestClient(app)


def login(username="webuser_0", password="pass"):
    return client.post("/login", json={
        "username": username,
        "password": password
    })


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestLogin:

    def setup_method(self):
        reset_attempts("testclient")

    def test_login_webuser_success(self):
        r = login("webuser_0")
        assert r.status_code == 200
        assert "token" in r.json()

    def test_login_mobileuser_success(self):
        r = login("mobileuser_1")
        assert r.status_code == 200

    def test_login_apiuser_success(self):
        r = login("apiuser_2")
        assert r.status_code == 200

    def test_login_wrong_password(self):
        r = login("webuser_0", "wrongpassword")
        assert r.status_code == 401

    def test_login_nonexistent_user(self):
        r = login("nobody", "pass")
        assert r.status_code == 401

    def test_login_old_users_gone(self):
        r = login("webuser", "pass")
        assert r.status_code == 401

    def test_rate_limit(self):
        for _ in range(20):
            client.post("/login", json={
                "username": "webuser_0",
                "password": "wrongpass"
            })
        r = login("webuser_0")
        assert r.status_code == 429


class TestMe:

    def setup_method(self):
        reset_attempts("testclient")

    def test_me_without_token(self):
        r = client.get("/me")
        assert r.status_code == 403

    def test_me_with_valid_token(self):
        token = login().json()["token"]
        r = client.get("/me", headers=auth_header(token))
        assert r.status_code == 200
        assert r.json()["role"] == "web"

    def test_me_with_invalid_token(self):
        r = client.get("/me", headers=auth_header("faketoken"))
        assert r.status_code == 401

    def test_mobile_user_role(self):
        token = login("mobileuser_1").json()["token"]
        r = client.get("/me", headers=auth_header(token))
        assert r.json()["role"] == "mobile"

    def test_api_user_role(self):
        token = login("apiuser_2").json()["token"]
        r = client.get("/me", headers=auth_header(token))
        assert r.json()["role"] == "api"


class TestProfileUpdate:

    def setup_method(self):
        reset_attempts("testclient")

    def test_update_profile_success(self):
        token = login().json()["token"]
        r = client.post("/profile/update",
            json={"display_name": "Test User", "email": "test@test.com"},
            headers=auth_header(token)
        )
        assert r.status_code == 200
        assert "display_name" in r.json()["updated_fields"]

    def test_update_profile_no_token(self):
        r = client.post("/profile/update", json={"display_name": "Test"})
        assert r.status_code == 403


class TestApiData:

    def setup_method(self):
        reset_attempts("testclient")

    def test_api_data_success(self):
        token = login().json()["token"]
        r = client.get("/api/data", headers=auth_header(token))
        assert r.status_code == 200
        assert r.json()["count"] == 50

    def test_api_data_no_token(self):
        r = client.get("/api/data")
        assert r.status_code == 403


class TestLogout:

    def setup_method(self):
        reset_attempts("testclient")

    def test_logout_success(self):
        token = login().json()["token"]
        r = client.post("/logout", headers=auth_header(token))
        assert r.status_code == 200

    def test_token_invalid_after_logout(self):
        token = login().json()["token"]
        client.post("/logout", headers=auth_header(token))
        r = client.get("/me", headers=auth_header(token))
        assert r.status_code == 401

    def test_logout_with_invalid_token(self):
        r = client.post("/logout", headers=auth_header("faketoken"))
        assert r.status_code == 401


class TestHealth:

    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestStats:

    def test_stats_shows_100_users(self):
        r = client.get("/stats")
        assert r.status_code == 200
        assert r.json()["total_users"] == 100