from pentest_platform.controllers.deps import get_actor, get_engagements
from pentest_platform.domain.entities import Engagement
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

ENGAGEMENT = Engagement(
    id="eng-1",
    name="Test",
    owner_id="user-1",
    authorization_ref="AUTH-1",
    authorization_valid=True,
    targets=["example.com"],
)


class StubEngagements:
    def create_engagement(self, actor, payload):
        return ENGAGEMENT

    def list_engagements(self, actor, page, page_size):
        return [ENGAGEMENT], {"page": page, "page_size": page_size, "total": 1, "pages": 1}

    def readiness(self, actor, engagement_id):
        return {"ready": True, "checks": [], "blocking": []}


def test_create_and_list_engagements():
    client = make_client({get_actor: lambda: actor(), get_engagements: lambda: StubEngagements()})
    created = client.post(
        "/api/v1/engagements",
        json={
            "name": "Test",
            "authorization_ref": "AUTH-1",
            "authorization_valid": True,
            "targets": ["example.com"],
        },
    )
    assert created.status_code == 201
    assert created.json()["id"] == "eng-1"
    listed = client.get("/api/v1/engagements")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["name"] == "Test"


def test_readiness_controller_maps_usecase_result():
    client = make_client({get_actor: lambda: actor(), get_engagements: lambda: StubEngagements()})
    response = client.get("/api/v1/engagements/eng-1/readiness")
    assert response.status_code == 200
    assert response.json()["ready"] is True
