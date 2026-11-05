import pytest

from pentest_platform.domain.entities import Assessment, Finding
from pentest_platform.domain.errors import ValidationError
from pentest_platform.usecases.scoring import ScoringUsecase
from tests.fakes import actor


def make_usecase(base_kwargs):
    return ScoringUsecase(**base_kwargs)


def create_finding(repo, ids, engagement):
    finding = Finding(
        id=ids.new_id(),
        engagement_id=engagement.id,
        run_id=None,
        title="XSS",
        affected_assets=["example.com"],
        state="VALIDATED",
    )
    repo.repo.add(finding)
    return finding


def test_cvss_is_deterministic_and_invalid_vectors_fail(base_kwargs, repo, ids, engagement):
    finding = create_finding(repo, ids, engagement)
    usecase = make_usecase(base_kwargs)
    assessment = usecase.update_cvss(
        actor(),
        finding.id,
        "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:N",
        {"AV": "network"},
    )
    assert assessment.cvss_score == 9.9
    assert assessment.cvss_rating == "Critical"
    with pytest.raises(ValidationError):
        usecase.update_cvss(actor(), finding.id, "not-a-vector", {})


def test_manual_override_requires_reason_and_survives_regeneration(base_kwargs, repo, ids, engagement):
    finding = create_finding(repo, ids, engagement)
    usecase = make_usecase(base_kwargs)
    with pytest.raises(ValidationError):
        usecase.override_severity(actor(), finding.id, "High", "")
    usecase.override_severity(actor(), finding.id, "High", "business context")
    usecase.reassess(actor(), finding.id, {"new_evidence": True})
    with usecase.uow_factory() as uow:
        stored = uow.repo.find_one(Assessment, finding_id=finding.id)
        assert stored.manual_severity == "High"
        assert stored.history


def test_business_risk_uses_active_policy(base_kwargs, repo, ids, engagement, risk_policy):
    finding = create_finding(repo, ids, engagement)
    usecase = make_usecase(base_kwargs)
    assessment = usecase.update_business_risk(actor(), finding.id, 4, 4, "material")
    assert assessment.business_band == "High"
    with pytest.raises(ValidationError):
        usecase.update_business_risk(actor(), finding.id, 9, 9, "bad")
