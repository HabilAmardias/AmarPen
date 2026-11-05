import pytest

from pentest_platform.domain.entities import Evidence, Finding
from pentest_platform.domain.errors import ConflictError
from pentest_platform.usecases.reports import ReportUsecase
from tests.fakes import actor


def make_usecase(base_kwargs, renderer, evidence_store):
    return ReportUsecase(**base_kwargs, renderer=renderer, evidence_store=evidence_store)


def add_validated_finding(repo, ids, engagement_id):
    finding = Finding(
        id=ids.new_id(),
        engagement_id=engagement_id,
        run_id=None,
        title="XSS",
        affected_assets=["example.com"],
        state="VALIDATED",
        expected_behavior="escaped",
        actual_behavior="reflected",
    )
    repo.repo.add(finding)
    repo.repo.add(
        Evidence(
            id=ids.new_id(),
            finding_id=finding.id,
            run_id=None,
            kind="request_response",
            storage_key="key",
            sha256="hash",
        )
    )
    return finding


def test_snapshot_requires_approval_before_render(base_kwargs, renderer, evidence_store, repo, ids, engagement):
    add_validated_finding(repo, ids, engagement.id)
    usecase = make_usecase(base_kwargs, renderer, evidence_store)
    report = usecase.create_snapshot(actor(), engagement.id)
    with pytest.raises(ConflictError):
        usecase.render(actor(), report.id)
    approved = usecase.approve(actor(roles=("Reviewer",)), report.id)
    assert approved.status == "FINAL_COMPLETE"
    rendered, pdf = usecase.render(actor(), report.id)
    assert pdf.startswith(b"%PDF")
    assert rendered.sha256


def test_download_verifies_integrity(base_kwargs, renderer, evidence_store, repo, ids, engagement):
    add_validated_finding(repo, ids, engagement.id)
    usecase = make_usecase(base_kwargs, renderer, evidence_store)
    report = usecase.create_snapshot(actor(), engagement.id)
    usecase.approve(actor(roles=("Reviewer",)), report.id)
    usecase.render(actor(), report.id)
    filename, content = usecase.download(actor(), report.id)
    assert filename.endswith(".pdf")
    assert content.startswith(b"%PDF")
