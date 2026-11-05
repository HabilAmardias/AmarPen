from pentest_platform.controllers.deps import get_access, get_actor
from tests.fakes import actor, user
from tests.unit.controllers.helpers import make_client


class StubAccess:
    def list_users(self, actor, page, page_size):
        return [user()], {"page": page, "page_size": page_size, "total": 1, "pages": 1}

    def create_user(self, actor, username, roles):
        return user(username=username), "temporary-password"

    def update_roles(self, actor, user_id, roles):
        item = user(roles=roles)
        return item

    def set_disabled(self, actor, user_id, disabled, reason):
        item = user()
        item.disabled = disabled
        return item

    def reset_mfa(self, actor, user_id, reason):
        item = user()
        item.totp_enabled = False
        return item

    def reset_password(self, actor, user_id, reason):
        return "new-temporary-password"


def test_access_user_endpoints():
    client = make_client({get_actor: lambda: actor(), get_access: lambda: StubAccess()})
    assert client.get("/api/v1/access/users").status_code == 200
    created = client.post("/api/v1/access/users", json={"username": "analyst1", "roles": ["Analyst"]})
    assert created.status_code == 201
    assert created.json()["temporary_password"] == "temporary-password"
    roles = client.put("/api/v1/access/users/user-1/roles", json={"roles": ["Reviewer"]})
    assert roles.json()["user"]["roles"] == ["Reviewer"]
    disabled = client.put("/api/v1/access/users/user-1/disabled", json={"disabled": True, "reason": "test"})
    assert disabled.json()["user"]["disabled"] is True
    mfa = client.post("/api/v1/access/users/user-1/reset-mfa")
    assert mfa.json()["user"]["totp_enabled"] is False
    password = client.post("/api/v1/access/users/user-1/reset-password")
    assert password.json()["temporary_password"] == "new-temporary-password"
