from pentest_platform.controllers.deps import get_actor, get_engagements
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client


class StubEngagements:
    def model_profile_options(self, actor):
        return [
            {
                "name": "local-default",
                "model": "mock-pentest",
                "data_boundary": "on_premises",
                "capabilities": ["chat", "structured_outputs"],
                "last_test_status": "REACHABLE",
                "last_tested_at": None,
            }
        ]


def test_model_profile_catalog_is_sanitized():
    client = make_client({get_actor: lambda: actor(), get_engagements: lambda: StubEngagements()})
    response = client.get("/api/v1/model-profiles")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["name"] == "local-default"
    assert "secret_ref" not in item
    assert "base_url" not in item
