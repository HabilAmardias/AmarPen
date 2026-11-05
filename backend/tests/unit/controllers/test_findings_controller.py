from pentest_platform.controllers.deps import get_actor, get_findings
from pentest_platform.domain.entities import Finding
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

FINDING = Finding(id="finding-1", engagement_id="eng-1", run_id=None, title="XSS", state="VALIDATED")


class StubFindings:
    def list_findings(self, actor, engagement_id, page, page_size, state):
        return [FINDING], {"page": page, "page_size": page_size, "total": 1, "pages": 1}

    def create_candidate(self, actor, engagement_id, payload):
        return FINDING

    def get_finding(self, actor, finding_id):
        return {"finding": FINDING, "evidence": [], "assessment": None, "retests": []}

    def validate_finding(self, actor, finding_id, verdict, reason):
        FINDING.state = verdict
        return FINDING

    def review_finding(self, actor, finding_id, decision, reason):
        return FINDING

    def start_retest(self, actor, engagement_id, finding_ids, notes, idempotency_key):
        from pentest_platform.domain.entities import RetestAttempt

        return RetestAttempt(id="retest-1", engagement_id=engagement_id, run_id="run-1", finding_ids=finding_ids)


def test_list_and_create_findings():
    client = make_client({get_actor: lambda: actor(), get_findings: lambda: StubFindings()})
    listed = client.get("/api/v1/engagements/eng-1/findings")
    assert listed.status_code == 200
    created = client.post("/api/v1/engagements/eng-1/findings", json={"title": "XSS"})
    assert created.status_code == 201
    detail = client.get("/api/v1/findings/finding-1")
    assert detail.json()["finding"]["title"] == "XSS"


def test_validate_and_start_retest():
    client = make_client({get_actor: lambda: actor(), get_findings: lambda: StubFindings()})
    validated = client.post("/api/v1/findings/finding-1/validate", json={"verdict": "VALIDATED", "reason": "ok"})
    assert validated.status_code == 200
    retest = client.post(
        "/api/v1/engagements/eng-1/retests",
        json={"finding_ids": ["finding-1"], "notes": "retest", "idempotency_key": "retest-1"},
    )
    assert retest.status_code == 202
    assert retest.json()["finding_ids"] == ["finding-1"]
