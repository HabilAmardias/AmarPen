from dataclasses import replace

from pentest_platform.controllers.deps import get_actor, get_admin, get_mcp
from pentest_platform.domain.entities import ModelProfile, RiskPolicy
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

PROFILE = ModelProfile(id="profile-1", name="local", base_url="http://localhost:8080/v1", model="mock")
POLICY = RiskPolicy(id="policy-1", name="Test", active=True)


class StubMcp:
    def list_servers(self, actor):
        return [{"stable_id": "local-mcp", "manifests": []}]

    def discover(self, actor, stable_id):
        from pentest_platform.domain.entities import McpToolManifest

        return McpToolManifest(id="manifest-2", server_id=stable_id, version=2, state="DRAFT")

    def activate_manifest(self, actor, manifest_id):
        from pentest_platform.domain.entities import McpToolManifest

        return McpToolManifest(id=manifest_id, server_id="local-mcp", version=2, state="ACTIVE")

    def ready(self):
        return {"ready": True, "checks": []}


class StubAdmin:
    def list_model_profiles(self, actor):
        return [PROFILE]

    def create_model_profile(self, actor, payload):
        return PROFILE

    def update_model_profile(self, actor, profile_id, payload):
        return PROFILE

    def test_model_profile(self, actor, profile_id):
        PROFILE.last_test_status = "REACHABLE"
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


class StubAdminWithSecret(StubAdmin):
    def __init__(self, profile):
        self.profile = profile

    def list_model_profiles(self, actor):
        return [self.profile]

    def create_model_profile(self, actor, payload):
        return self.profile

    def update_model_profile(self, actor, profile_id, payload):
        return self.profile

    def test_model_profile(self, actor, profile_id):
        return self.profile


def test_model_profile_and_risk_policy_admin_endpoints():
    client = make_client({get_actor: lambda: actor(), get_admin: lambda: StubAdmin()})
    profiles = client.get("/api/v1/admin/model-profiles")
    assert profiles.json()["items"][0]["name"] == "local"
    created = client.post(
        "/api/v1/admin/model-profiles",
        json={"name": "local", "base_url": "http://localhost:8080/v1", "model": "mock"},
    )
    assert created.status_code == 201
    tested = client.post("/api/v1/admin/model-profiles/profile-1/test")
    assert tested.status_code == 200
    assert tested.json()["last_test_status"] == "REACHABLE"
    policies = client.get("/api/v1/admin/risk-policies")
    assert policies.json()["items"][0]["active"] is True
    activated = client.post("/api/v1/admin/risk-policies/policy-1/activate")
    assert activated.status_code == 200


def test_model_profile_endpoints_hide_credentials():
    secret_profile = replace(PROFILE, api_key_encrypted="enc:secret", secret_ref="env:API_KEY")
    client = make_client({get_actor: lambda: actor(), get_admin: lambda: StubAdminWithSecret(secret_profile)})
    response = client.get("/api/v1/admin/model-profiles")
    item = response.json()["items"][0]
    assert item["has_api_key"] is True
    assert item["credential_source"] == "stored"
    assert "api_key" not in item
    assert "api_key_encrypted" not in item
    assert "secret_ref" not in item


def test_mcp_admin_endpoints():
    client = make_client({get_actor: lambda: actor(), get_admin: lambda: StubAdmin(), get_mcp: lambda: StubMcp()})
    assert client.get("/api/v1/admin/mcp/servers").json()["items"][0]["stable_id"] == "local-mcp"
    discovered = client.post("/api/v1/admin/mcp/servers/local-mcp/discover")
    assert discovered.json()["state"] == "DRAFT"
    activated = client.post("/api/v1/admin/mcp/manifests/manifest-2/activate")
    assert activated.json()["state"] == "ACTIVE"
    assert client.get("/api/v1/admin/mcp/ready").json()["ready"] is True


def test_setting_update_endpoint():
    client = make_client({get_actor: lambda: actor(), get_admin: lambda: StubAdmin()})
    response = client.put("/api/v1/admin/settings/session.timeout", json={"value": {"minutes": 30}})
    assert response.status_code == 200
    assert response.json()["key"] == "session.timeout"
