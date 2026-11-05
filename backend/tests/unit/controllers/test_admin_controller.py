from pentest_platform.controllers.deps import get_actor, get_admin
from pentest_platform.domain.entities import ModelProfile, RiskPolicy
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

PROFILE = ModelProfile(id="profile-1", name="local", base_url="http://localhost:8080/v1", model="mock")
POLICY = RiskPolicy(id="policy-1", name="Test", active=True)


class StubAdmin:
    def list_model_profiles(self, actor):
        return [PROFILE]

    def create_model_profile(self, actor, payload):
        return PROFILE

    def update_model_profile(self, actor, profile_id, payload):
        return PROFILE

    def list_risk_policies(self, actor):
        return [POLICY]

    def create_risk_policy(self, actor, name, matrix, bands):
        return POLICY

    def activate_risk_policy(self, actor, policy_id):
        return POLICY

    def list_settings(self, actor):
        return []

    def update_setting(self, actor, key, value):
        from pentest_platform.domain.entities import ConfigSetting

        return ConfigSetting(id="setting-1", key=key, value=value)


def test_model_profile_and_risk_policy_admin_endpoints():
    client = make_client({get_actor: lambda: actor(), get_admin: lambda: StubAdmin()})
    profiles = client.get("/api/v1/admin/model-profiles")
    assert profiles.json()["items"][0]["name"] == "local"
    created = client.post(
        "/api/v1/admin/model-profiles",
        json={"name": "local", "base_url": "http://localhost:8080/v1", "model": "mock"},
    )
    assert created.status_code == 201
    policies = client.get("/api/v1/admin/risk-policies")
    assert policies.json()["items"][0]["active"] is True
    activated = client.post("/api/v1/admin/risk-policies/policy-1/activate")
    assert activated.status_code == 200


def test_setting_update_endpoint():
    client = make_client({get_actor: lambda: actor(), get_admin: lambda: StubAdmin()})
    response = client.put("/api/v1/admin/settings/session.timeout", json={"value": {"minutes": 30}})
    assert response.status_code == 200
    assert response.json()["key"] == "session.timeout"
