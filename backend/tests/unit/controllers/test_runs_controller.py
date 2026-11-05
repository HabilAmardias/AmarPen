from pentest_platform.controllers.deps import get_actor, get_runs
from pentest_platform.domain.entities import Run
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

RUN = Run(id="run-1", engagement_id="eng-1", state="QUEUED", initiated_by="user-1")


class StubRuns:
    def start(self, actor, engagement_id, idempotency_key, reason=""):
        return RUN

    def get_run(self, actor, run_id):
        return RUN

    def list_runs(self, actor, engagement_id):
        return [RUN]

    def pause(self, actor, run_id, idempotency_key):
        RUN.state = "PAUSING"
        return RUN

    def agent_activity(self, actor, run_id):
        return {"tasks": [], "results": [], "proposals": [], "assets": []}


def test_start_returns_accepted_current_state():
    client = make_client({get_actor: lambda: actor(), get_runs: lambda: StubRuns()})
    response = client.post("/api/v1/runs/engagements/eng-1/start", json={"idempotency_key": "idem-1"})
    assert response.status_code == 202
    assert response.json()["state"] == "QUEUED"
    detail = client.get("/api/v1/runs/run-1")
    assert detail.status_code == 200


def test_agent_activity_is_exposed():
    client = make_client({get_actor: lambda: actor(), get_runs: lambda: StubRuns()})
    response = client.get("/api/v1/runs/run-1/agents")
    assert response.status_code == 200
    assert response.json()["tasks"] == []


def test_pause_returns_pausing_not_paused():
    client = make_client({get_actor: lambda: actor(), get_runs: lambda: StubRuns()})
    response = client.post("/api/v1/runs/run-1/pause", json={"idempotency_key": "pause-1"})
    assert response.status_code == 202
    assert response.json()["state"] == "PAUSING"
