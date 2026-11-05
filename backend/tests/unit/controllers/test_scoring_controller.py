from pentest_platform.controllers.deps import get_actor, get_scoring
from pentest_platform.domain.entities import Assessment
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

ASSESSMENT = Assessment(id="assessment-1", finding_id="finding-1", cvss_score=9.9, cvss_rating="Critical")


class StubScoring:
    def get_assessment(self, actor, finding_id):
        return ASSESSMENT

    def update_cvss(self, actor, finding_id, vector, rationale, expected_version):
        ASSESSMENT.cvss_vector = vector
        return ASSESSMENT

    def override_severity(self, actor, finding_id, severity, reason):
        ASSESSMENT.manual_severity = severity
        return ASSESSMENT

    def update_business_risk(self, actor, finding_id, likelihood, impact, rationale, policy_id):
        ASSESSMENT.business_band = "High"
        return ASSESSMENT


def test_get_and_update_cvss():
    client = make_client({get_actor: lambda: actor(), get_scoring: lambda: StubScoring()})
    assert client.get("/api/v1/findings/finding-1/assessment").status_code == 200
    response = client.put(
        "/api/v1/findings/finding-1/assessment/cvss",
        json={"vector": "CVSS:4.0/AV:N", "rationale": {"AV": "network"}},
    )
    assert response.status_code == 200
    assert response.json()["cvss_vector"] == "CVSS:4.0/AV:N"


def test_override_and_business_risk():
    client = make_client({get_actor: lambda: actor(), get_scoring: lambda: StubScoring()})
    override = client.post(
        "/api/v1/findings/finding-1/assessment/override",
        json={"severity": "High", "reason": "business"},
    )
    assert override.status_code == 200
    risk = client.put(
        "/api/v1/findings/finding-1/assessment/business-risk",
        json={"likelihood": 4, "impact": 4, "rationale": "material"},
    )
    assert risk.json()["business_band"] == "High"
