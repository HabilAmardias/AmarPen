import pytest

from pentest_platform.domain.entities import (
    Finding,
    Run,
    Scenario,
)
from pentest_platform.domain.errors import ConflictError, ValidationError
from pentest_platform.usecases.access import AccessUsecase
from pentest_platform.usecases.admin import AdminUsecase
from pentest_platform.usecases.audit import AuditUsecase
from pentest_platform.usecases.engagements import EngagementUsecase
from pentest_platform.usecases.findings import FindingUsecase
from pentest_platform.usecases.prompts import PromptUsecase
from pentest_platform.usecases.reports import ReportUsecase
from pentest_platform.usecases.runs import RunUsecase
from pentest_platform.usecases.scoring import ScoringUsecase
from pentest_platform.usecases.testing import TestingUsecase
from tests.fakes import FakeLlmGateway, FakeSecretCipher, actor, user


def test_engagement_listing_update_member_and_status(base_kwargs, evidence_store, engagement, repo, ids):
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    listed, meta = usecase.list_engagements(actor())
    assert meta["total"] == 1
    original_scope = engagement.scope_version
    updated = usecase.update_engagement(actor(), engagement.id, {"name": "Renamed", "targets": ["example.org"]}, engagement.config_version)
    assert updated.name == "Renamed"
    assert updated.scope_version == original_scope + 1
    member_user = user(user_id="user-2", username="member")
    repo.repo.add(member_user)
    member = usecase.add_member(actor(), engagement.id, "user-2", "Reviewer")
    assert member.access_role == "Reviewer"
    status = usecase.set_status(actor(), engagement.id, "READY")
    assert status.status == "READY"


def test_engagement_plan_selects_applicable_scenario(base_kwargs, evidence_store, engagement, repo, ids):
    repo.repo.add(Scenario(id=ids.new_id(), key="WSTG-INFO-01", version="1.0", title="Info"))
    result = EngagementUsecase(**base_kwargs, evidence_store=evidence_store).plan(actor(), engagement.id)
    assert result["selected"][0]["key"] == "WSTG-INFO-01"


def test_findings_listing_and_review(base_kwargs, evidence_store, engagement, repo, ids):
    finding = Finding(id=ids.new_id(), engagement_id=engagement.id, run_id=None, title="XSS", state="VALIDATED")
    repo.repo.add(finding)
    usecase = FindingUsecase(**base_kwargs, evidence_store=evidence_store)
    items, meta = usecase.list_findings(actor(), engagement.id)
    assert meta["total"] == 1
    reviewed = usecase.review_finding(actor(roles=("Reviewer",)), finding.id, "approve", "ok")
    assert reviewed.state == "REVIEWED"


def test_finding_retest_outcome_with_evidence(base_kwargs, evidence_store, engagement, active_release, repo, ids):
    finding = Finding(id=ids.new_id(), engagement_id=engagement.id, run_id=None, title="XSS", state="VALIDATED")
    repo.repo.add(finding)
    usecase = FindingUsecase(**base_kwargs, evidence_store=evidence_store)
    attempt = usecase.start_retest(actor(), engagement.id, [finding.id], "retest", "retest-1")
    updated = usecase.record_retest_outcome(actor(), attempt.id, finding.id, "FIXED", "patched", b"new evidence")
    assert updated.state == "COMPLETED"
    assert repo.repo.get(Finding, finding.id).latest_retest_outcome == "FIXED"
    assert usecase.list_retests(actor(), engagement.id)


def test_run_conflicts_and_failures(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, ids):
    usecase = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner)
    run = usecase.start(actor(), engagement.id, "start-1")
    with pytest.raises(ConflictError):
        usecase.start(actor(), engagement.id, "start-2")
    with pytest.raises(ConflictError):
        usecase.pause(actor(), run.id, "pause-invalid")
    stored = repo.repo.get(Run, run.id)
    stored.state = "COMPLETED"
    repo.repo.update(stored)
    with pytest.raises(ConflictError):
        usecase.stop(actor(), run.id, "stop-completed")


def test_prompt_management_extended(base_kwargs):
    usecase = PromptUsecase(**base_kwargs)
    prompt = usecase.create_draft(actor(), "agent-test", "orchestrator", "purpose", "Act safely.", "initial")
    updated = usecase.update_draft(actor(), prompt.id, "Act carefully.", "improved", prompt.version)
    assert updated.body == "Act carefully."
    validation = usecase.validate_prompt(actor(), updated.id)
    assert validation["passed"] is True
    published = usecase.publish(actor(), updated.id)
    assert published.content_hash
    assert usecase.list_prompts(actor(), include_bodies=True)[0]["body"] == "Act carefully."
    assert usecase.get_prompt(actor(), published.id)["key"] == "agent-test"
    with pytest.raises(ValidationError):
        usecase.create_release(actor(), "bad", {"orchestrator": "missing"})


def test_prompt_retire_and_rollback(base_kwargs):
    from pentest_platform.domain.agents import REQUIRED_AGENT_ROLES
    usecase = PromptUsecase(**base_kwargs)
    manifest = {}
    for role in sorted(REQUIRED_AGENT_ROLES):
        prompt = usecase.create_draft(actor(), f"agent-{role}", role, "purpose", "Act safely.", "initial")
        usecase.publish(actor(), prompt.id)
        manifest[role] = prompt.id
    release = usecase.create_release(actor(), "release-1", manifest)
    usecase.validate_release(actor(), release.id)
    active = usecase.activate_release(actor(), release.id)
    assert active.state == "ACTIVE"
    rolled = usecase.rollback_release(actor(), release.id, "rollback")
    assert rolled.state == "ACTIVE"
    with pytest.raises(ConflictError):
        usecase.retire(actor(), manifest["orchestrator"])


def test_report_preview_and_listing(base_kwargs, renderer, evidence_store, engagement):
    usecase = ReportUsecase(**base_kwargs, renderer=renderer, evidence_store=evidence_store)
    report = usecase.create_snapshot(actor(), engagement.id)
    assert usecase.list_reports(actor(), engagement.id)[0].id == report.id
    assert usecase.get_report(actor(), report.id).id == report.id
    assert usecase.preview(actor(), report.id).startswith(b"%PDF")


def test_admin_update_profile_and_settings(base_kwargs):
    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(), secret_cipher=FakeSecretCipher())
    profile = usecase.create_model_profile(
        actor(),
        {"name": "local", "base_url": "http://localhost:8080/v1", "model": "mock"},
    )
    updated = usecase.update_model_profile(actor(), profile.id, {"enabled": False})
    assert updated.enabled is False
    usecase.update_setting(actor(), "session.timeout", {"minutes": 30})
    assert usecase.list_settings(actor())[0].key == "session.timeout"


def test_access_update_roles_and_password(base_kwargs, passwords, repo):
    usecase = AccessUsecase(**base_kwargs, passwords=passwords)
    target, _ = usecase.create_user(actor(), "analyst1", ["Analyst"])
    updated = usecase.update_roles(actor(), target.id, ["Reviewer"])
    assert updated.roles == ["Reviewer"]
    with pytest.raises(ValidationError):
        usecase.change_own_password(actor(user_id=target.id), "wrong", "correct horse battery", "token")


def test_scoring_restore_and_effective(base_kwargs, repo, ids, engagement):
    finding = Finding(id=ids.new_id(), engagement_id=engagement.id, run_id=None, title="XSS", state="VALIDATED")
    repo.repo.add(finding)
    usecase = ScoringUsecase(**base_kwargs)
    usecase.update_cvss(
        actor(),
        finding.id,
        "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:N",
        {"AV": "network"},
    )
    usecase.override_severity(actor(), finding.id, "High", "business")
    assert usecase.effective_severity(actor(), finding.id) == "High"
    restored = usecase.restore_platform_assessment(actor(), finding.id)
    assert restored.manual_severity == ""
    assert usecase.get_assessment(actor(), finding.id) is not None


def test_audit_date_filters(base_kwargs, repo, clock, ids):
    from pentest_platform.domain.entities import AuditEvent

    event = AuditEvent(
        id=ids.new_id(),
        event_id=ids.new_id(),
        occurred_at=clock.now(),
        recorded_at=clock.now(),
        actor_type="user",
        actor_id="user-1",
        action="test",
        resource="x",
        outcome="SUCCESS",
    )
    repo.repo.add(event)
    usecase = AuditUsecase(**base_kwargs)
    events, _ = usecase.search(actor(), {"start": clock.now(), "end": clock.now()})
    assert len(events) == 1


def test_testing_coverage_empty(base_kwargs, engagement):
    result = TestingUsecase(**base_kwargs).coverage(actor(), engagement.id)
    assert result["records"] == []
