import pytest

from pentest_platform.domain.entities import Finding
from pentest_platform.domain.errors import ConflictError, ForbiddenError, ValidationError
from pentest_platform.usecases.findings import FindingUsecase
from tests.fakes import actor


def make_usecase(base_kwargs, evidence_store):
    return FindingUsecase(**base_kwargs, evidence_store=evidence_store)


def create_finding(usecase, engagement_id):
    return usecase.create_candidate(
        actor(),
        engagement_id,
        {
            "title": "Reflected XSS",
            "affected_assets": ["example.com"],
            "actual_behavior": "payload reflected",
        },
    )


def test_candidate_requires_edit_permission(base_kwargs, evidence_store, engagement):
    usecase = make_usecase(base_kwargs, evidence_store)
    with pytest.raises(ForbiddenError):
        usecase.create_candidate(actor(roles=("Viewer",)), engagement.id, {"title": "X"})


def test_duplicate_candidates_are_rejected(base_kwargs, evidence_store, engagement):
    usecase = make_usecase(base_kwargs, evidence_store)
    create_finding(usecase, engagement.id)
    with pytest.raises(ConflictError):
        create_finding(usecase, engagement.id)


def test_validation_requires_evidence(base_kwargs, evidence_store, engagement):
    usecase = make_usecase(base_kwargs, evidence_store)
    finding = create_finding(usecase, engagement.id)
    with pytest.raises(ValidationError):
        usecase.validate_finding(actor(), finding.id, "VALIDATED", "no evidence")


def test_evidence_and_validation_succeed(base_kwargs, evidence_store, engagement):
    usecase = make_usecase(base_kwargs, evidence_store)
    finding = create_finding(usecase, engagement.id)
    evidence = usecase.add_evidence(actor(), finding.id, "request_response", b"HTTP/1.1 200 OK")
    assert evidence.sha256
    validated = usecase.validate_finding(actor(), finding.id, "VALIDATED", "reproduced")
    assert validated.state == "VALIDATED"
    retrieved, content = usecase.get_evidence(actor(), evidence.id)
    assert content == b"HTTP/1.1 200 OK"


def test_edit_uses_optimistic_version(base_kwargs, evidence_store, engagement):
    usecase = make_usecase(base_kwargs, evidence_store)
    finding = create_finding(usecase, engagement.id)
    original_version = finding.version
    updated = usecase.edit_finding(actor(), finding.id, {"title": "Updated"}, original_version)
    assert updated.version == original_version + 1
    with pytest.raises(ConflictError):
        usecase.edit_finding(actor(), finding.id, {"title": "Again"}, original_version)


def test_retest_preserves_original_and_requires_evidence(base_kwargs, evidence_store, engagement, active_release):
    usecase = make_usecase(base_kwargs, evidence_store)
    finding = create_finding(usecase, engagement.id)
    original = finding.version
    attempt = usecase.start_retest(actor(), engagement.id, [finding.id], "remediated", "retest-1")
    assert attempt.finding_ids == [finding.id]
    with pytest.raises(ValidationError):
        usecase.record_retest_outcome(actor(), attempt.id, finding.id, "FIXED", "no evidence")
    updated = usecase.record_retest_outcome(actor(), attempt.id, finding.id, "INCONCLUSIVE", "blocked", None)
    assert updated.outcomes[finding.id] == "INCONCLUSIVE"
    assert repo_finding_version(usecase, finding.id) == original


def repo_finding_version(usecase, finding_id):
    with usecase.uow_factory() as uow:
        return uow.repo.get(Finding, finding_id).version
