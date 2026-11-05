from pentest_platform.controllers.deps import get_auth
from pentest_platform.domain.entities import Session
from pentest_platform.usecases.auth import AuthResult
from tests.fakes import actor, user
from tests.unit.controllers.helpers import make_client


class StubAuth:
    def login(self, username, password, source):
        session = Session(id="session-1", user_id="user-1", token_hash="h", csrf_token="csrf-1")
        return AuthResult("session-token", "csrf-1", user(), session, requires_totp=True)

    def bootstrap(self, token, username, password):
        return user()

    def current_session(self, token):
        return AuthResult(token, "csrf-1", user(), Session(id="s", user_id="user-1", token_hash="h", csrf_token="csrf-1"))

    def logout(self, token):
        return None


def test_login_maps_credentials_and_sets_cookies():
    client = make_client({get_auth: lambda: StubAuth()})
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "correct horse battery"})
    assert response.status_code == 200
    assert response.json()["requires_totp"] is True
    assert "pt_session" in response.cookies
    assert "pt_csrf" in response.cookies


def test_bootstrap_maps_created_user():
    client = make_client({get_auth: lambda: StubAuth()})
    response = client.post(
        "/api/v1/auth/bootstrap",
        json={"bootstrap_token": "boot", "username": "admin", "password": "correct horse battery"},
    )
    assert response.status_code == 201
    assert response.json()["user"]["username"] == "admin"


def test_session_returns_authenticated_actor():
    from pentest_platform.controllers.deps import get_actor

    client = make_client({get_auth: lambda: StubAuth(), get_actor: lambda: actor()})
    response = client.get("/api/v1/auth/session")
    assert response.status_code == 200
    assert response.json()["csrf_token"] == "csrf-1"
