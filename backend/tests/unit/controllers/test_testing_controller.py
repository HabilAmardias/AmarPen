from pentest_platform.controllers.deps import get_actor, get_testing
from pentest_platform.domain.entities import Scenario
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

SCENARIO = Scenario(id="scenario-1", key="WSTG-INFO-01", version="1.0", title="Info")


class StubTesting:
    def list_scenarios(self, actor):
        return [SCENARIO]

    def coverage(self, actor, engagement_id):
        return {"counts": {}, "records": []}


def test_scenarios_and_coverage_endpoints():
    client = make_client({get_actor: lambda: actor(), get_testing: lambda: StubTesting()})
    scenarios = client.get("/api/v1/testing/scenarios")
    assert scenarios.status_code == 200
    assert scenarios.json()["items"][0]["key"] == "WSTG-INFO-01"
    coverage = client.get("/api/v1/testing/engagements/eng-1/coverage")
    assert coverage.status_code == 200
