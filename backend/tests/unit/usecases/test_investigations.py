"""Regression tests for bounded specialist investigations and request fidelity."""

from types import SimpleNamespace

import pytest

from pentest_platform.adapters.tools.endpoint_crawler import _safe_url
from pentest_platform.domain.entities import (
    AgentProposal,
    AssetRecord,
    BudgetLedger,
    CoverageRecord,
    Finding,
    Run,
    Scenario,
    Task,
)
from pentest_platform.domain.entities import (
    TestIdentity as Identity,
)
from pentest_platform.usecases.agent_runtime import AgentExecutionUsecase
from pentest_platform.usecases.agent_scheduler import AgentSchedulerUsecase
from pentest_platform.usecases.runs import RunUsecase
from tests.fakes import FakeLlmGateway, actor


class StubMcp:
    def __init__(self, status=200):
        self.calls = []
        self.status = status
        self.mcp_host = self

    def tool_definitions(self, run, role):
        return [
            {"name": tool, "input_schema": {"type": "object"}}
            for tool in ["http_request", "http_probe", "map_endpoints"]
        ]

    def issue_authority(self, *args):
        return "unit-test-authority"

    def call_tool(self, tool, arguments, authority):
        self.calls.append((tool, arguments))
        return {"result": {"outcome": "COMPLETED", "status_code": self.status}, "evidence_refs": []}


def start(base_kwargs, evidence_store, tool_runner, engagement, repo, plan=None, output=None, status=200):
    repo.repo.add(
        Scenario(
            id="review-scenario",
            key="WSTG-INPV-01",
            version="1",
            title="Input check",
            agent_role="web_testing",
            side_effects=["read_only"],
            applicability={"allowed_methods": ["POST"]},
        )
    )
    plan = plan or [
        {
            "role": "web_testing",
            "kind": "test",
            "scenario_key": "WSTG-INPV-01",
            "asset": "https://example.com/search",
            "reason": "Inspect input",
        }
    ]
    llm = FakeLlmGateway(
        responses={
            "orchestrator": {"tasks": plan},
            "web_testing": output or {"candidates": [], "coverage_status": "INCONCLUSIVE"},
        }
    )
    mcp = StubMcp(status)
    executor = AgentExecutionUsecase(
        **base_kwargs, llm_gateway=llm, evidence_store=evidence_store, tool_runner=tool_runner, mcp=mcp
    )
    scheduler = AgentSchedulerUsecase(**base_kwargs, executor=executor)
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(
        actor(), engagement.id, "review-start"
    )
    scheduler.tick("review-worker", limit=8)
    return run, executor, scheduler, llm, mcp


def test_specialist_observes_a_second_action_before_finishing(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    outputs = [
        {
            "decision": "TOOL_ACTION",
            "tool": "http_request",
            "arguments": {"target": "https://example.com/search?q=marker", "method": "GET"},
            "reason": "Compare the baseline with a permitted input",
        },
        {
            "decision": "FINISH",
            "reason": "Baseline and comparison agree",
            "candidates": [],
            "coverage_status": "TESTED_NO_ISSUE_OBSERVED",
        },
    ]
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, output=outputs
    )
    scheduler.tick("review-worker", limit=8)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    assert task.state == "QUEUED"
    assert task.checkpoint["pending_action"]["decision"] == "TOOL_ACTION"
    # Recreate the executor/scheduler to exercise recovery from durable state.
    restarted = AgentExecutionUsecase(
        **base_kwargs, llm_gateway=llm, evidence_store=evidence_store, tool_runner=tool_runner, mcp=mcp
    )
    AgentSchedulerUsecase(**base_kwargs, executor=restarted).tick("new-worker", limit=8)
    assert len(mcp.calls) == 2
    assert mcp.calls[1][1]["target"].endswith("?q=marker")
    assert repo.repo.get(Task, task.id).state == "COMPLETED"
    calls = [call for call in llm.calls if call["role"] == "web_testing"]
    assert len(calls) == 2
    assert len(calls[1]["context"]["observations"]) == 2
    assert calls[1]["context"]["permitted_tools"]
    assert calls[1]["context"]["remaining_budgets"]
    assert repo.repo.list(AgentProposal, run_id=run.id, kind="tool_action")[0].status == "APPROVED"


def test_planned_body_is_forwarded_to_mcp(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    plan = [
        {
            "role": "web_testing",
            "kind": "test",
            "scenario_key": "WSTG-INPV-01",
            "asset": "https://example.com/search",
            "method": "POST",
            "body": '{"q":"benign-marker"}',
            "content_type": "application/json",
            "reason": "Input check",
        }
    ]
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, plan=plan
    )
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    assert task.input_records["body"]
    scheduler.tick("review-worker", limit=8)
    assert mcp.calls[0][1]["method"] == "POST"
    assert mcp.calls[0][1]["body"] == task.input_records["body"]
    assert mcp.calls[0][1]["content_type"] == "application/json"


def test_method_and_identity_variants_remain_distinct(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    base = {
        "role": "web_testing",
        "kind": "test",
        "scenario_key": "WSTG-INPV-01",
        "asset": "https://example.com/search",
        "reason": "Comparison",
    }
    run, *_ = start(
        base_kwargs,
        evidence_store,
        tool_runner,
        engagement,
        repo,
        plan=[
            {**base, "method": "GET", "identity_id": "identity-a"},
            {**base, "method": "POST", "identity_id": "identity-b"},
        ],
    )
    assert len(repo.repo.list(Task, run_id=run.id, role="web_testing")) == 2


def test_503_concludes_specialist_without_investigation_followup(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, status=503
    )
    scheduler.tick("review-worker", limit=8)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    assert task.state == "COMPLETED"
    assert len(mcp.calls) == 1
    assert repo.repo.find_one(CoverageRecord, run_id=run.id).status == "INCONCLUSIVE"
    assert not [
        t
        for t in repo.repo.list(Task, run_id=run.id)
        if t.role == "orchestrator" and t.id != repo.repo.list(Task, run_id=run.id)[0].id
    ]


def test_discovery_only_run_is_explicitly_partial(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    llm = FakeLlmGateway()
    executor = AgentExecutionUsecase(
        **base_kwargs, llm_gateway=llm, evidence_store=evidence_store, tool_runner=tool_runner
    )
    scheduler = AgentSchedulerUsecase(**base_kwargs, executor=executor)
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(
        actor(), engagement.id, "review-discovery-only"
    )
    for _ in range(6):
        scheduler.tick("review-worker", limit=8)
    assert repo.repo.get(Run, run.id).state == "FAILED"
    assert repo.repo.get(Run, run.id).config_snapshot["assessment_completeness"] == "PARTIAL"
    assert not [
        t
        for t in repo.repo.list(Task, run_id=run.id)
        if t.role in {"web_testing", "api_testing", "authorization_business_logic"}
    ]


def test_validation_requires_controlled_candidate_reentry(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, *_ = start(base_kwargs, evidence_store, tool_runner, engagement, repo)
    finding = Finding(
        id="review-finding",
        engagement_id=engagement.id,
        run_id=run.id,
        title="Evidence gap",
        state="INCONCLUSIVE",
        version=2,
    )
    repo.repo.add(finding)
    with executor.uow_factory() as uow:
        ok, reason = executor._apply_validation(
            uow,
            SimpleNamespace(),
            run,
            engagement,
            SimpleNamespace(input_records={"expected_version": 2}),
            {"verdict": "INCONCLUSIVE", "rationale": "New evidence"},
            finding.id,
        )
    assert not ok
    assert "Only candidate" in reason


def test_crawler_preserves_query_variants():
    assert _safe_url("https://example.com/", "/search?q=one", ["example.com"], []) != _safe_url(
        "https://example.com/", "/search?q=two", ["example.com"], []
    )


def test_fallback_does_not_spend_validation_iteration_budget(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, *_ = start(base_kwargs, evidence_store, tool_runner, engagement, repo)
    repo.repo.add(
        Scenario(
            id="review-api-scenario",
            key="API-2023-01",
            version="1",
            title="Object authorization",
            agent_role="api_testing",
            side_effects=["read_only"],
        )
    )
    for identity in ["a", "b"]:
        repo.repo.add(
            Identity(
                id=f"identity-{identity}",
                engagement_id=engagement.id,
                label=identity,
                role="user",
                enabled=True,
            )
        )
    for index in range(12):
        repo.repo.add(
            AssetRecord(
                id=f"endpoint-{index}",
                run_id=run.id,
                engagement_id=engagement.id,
                kind="endpoint",
                value=f"https://example.com/api/resource/{index}",
                asset_metadata={"status_code": 200, "content_type": "application/json", "methods": ["GET"]},
            )
        )
    parent = repo.repo.list(Task, run_id=run.id)[0]
    with executor.uow_factory() as uow:
        executor._schedule_fallback_endpoint_tests(uow, run, engagement, parent)
        finding = Finding(
            id="starved-finding",
            engagement_id=engagement.id,
            run_id=run.id,
            title="Needs validation",
            state="CANDIDATE",
        )
        uow.repo.add(finding)
        executor._schedule_validation(uow, run, engagement, finding)
    ledger = repo.repo.find_one(BudgetLedger, run_id=run.id)
    assert ledger.iteration_used == 0
    assert repo.repo.list(Task, run_id=run.id, role="validation")


def action(target="https://example.com/search?q=next"):
    return {
        "decision": "TOOL_ACTION",
        "tool": "http_request",
        "arguments": {"target": target, "method": "GET"},
        "reason": "Obtain a comparison",
    }


def final():
    return {
        "decision": "FINISH",
        "reason": "Required comparisons have been observed",
        "candidates": [],
        "coverage_status": "TESTED_NO_ISSUE_OBSERVED",
    }


def test_transient_failure_can_recover_with_bounded_delayed_retry(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, clock
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs,
        evidence_store,
        tool_runner,
        engagement,
        repo,
        output=[action("https://example.com/search"), final()],
        status=503,
    )
    scheduler.tick("review-worker", limit=8)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    assert task.state == "QUEUED"
    assert task.next_attempt_at > clock.now()
    mcp.status = 200
    clock.advance(seconds=5)
    scheduler.tick("review-worker", limit=8)
    assert len(mcp.calls) == 2
    assert repo.repo.find_one(CoverageRecord, run_id=run.id).status == "TESTED_NO_ISSUE_OBSERVED"


def test_repeated_successful_action_is_stopped_without_replay(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs,
        evidence_store,
        tool_runner,
        engagement,
        repo,
        output=action("https://example.com/search"),
    )
    scheduler.tick("review-worker", limit=8)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    assert "already observed" in task.checkpoint["stop_reason"]
    assert len(mcp.calls) == 1


def test_missing_prerequisite_is_a_durable_visible_outcome(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    output = {
        "decision": "NEEDS_PREREQUISITE",
        "prerequisite": "Second approved test identity",
        "reason": "Ownership comparison requires two sessions",
    }
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, output=output
    )
    scheduler.tick("review-worker", limit=8)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    assert task.outcome == "INCONCLUSIVE"
    assert "Second approved" in task.checkpoint["stop_reason"]
    assert repo.repo.find_one(CoverageRecord, run_id=run.id).status == "INCONCLUSIVE"


def test_model_json_repair_does_not_repeat_completed_http(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, clock
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, output=[{"unexpected": True}, final()]
    )
    scheduler.tick("review-worker", limit=8)
    clock.advance(seconds=5)
    scheduler.tick("review-worker", limit=8)
    assert len(mcp.calls) == 1
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    assert task.state == "COMPLETED" and task.outcome == "SUCCEEDED"
    assert len([c for c in llm.calls if c["role"] == "web_testing"]) == 2


def test_out_of_scope_followup_is_denied_before_target_io(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs,
        evidence_store,
        tool_runner,
        engagement,
        repo,
        output=action("https://outside.example.net/"),
    )
    scheduler.tick("review-worker", limit=8)
    assert len(mcp.calls) == 1
    proposal = repo.repo.find_one(AgentProposal, run_id=run.id, kind="tool_action")
    assert proposal.status == "DENIED"
    assert "scope" in proposal.decision_reason


def test_unapproved_post_is_blocked_before_io(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(base_kwargs, evidence_store, tool_runner, engagement, repo)
    scenario = repo.repo.get(Scenario, "review-scenario")
    scenario.applicability = {}
    repo.repo.update(scenario)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    task.method = "POST"
    repo.repo.update(task)
    scheduler.tick("review-worker", limit=8)
    assert not mcp.calls
    assert "explicitly approved" in repo.repo.get(Task, task.id).checkpoint["stop_reason"]


def test_pause_during_tool_wait_prevents_next_model_call(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, output=action()
    )
    original = mcp.call_tool

    def pause_then_respond(*args):
        current = repo.repo.get(Run, run.id)
        current.state = "PAUSING"
        repo.repo.update(current)
        return original(*args)

    mcp.call_tool = pause_then_respond
    scheduler.tick("review-worker", limit=8)
    assert not [c for c in llm.calls if c["role"] == "web_testing"]
    assert repo.repo.find_one(Task, run_id=run.id, role="web_testing").state == "PAUSED"
    assert len(mcp.calls) == 1


def test_stop_during_model_wait_cannot_dispatch_followup(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, output=action()
    )
    original = llm.complete

    def stop_then_respond(*args):
        current = repo.repo.get(Run, run.id)
        current.state = "STOPPING"
        repo.repo.update(current)
        return original(*args)

    llm.complete = stop_then_respond
    scheduler.tick("review-worker", limit=8)
    assert len(mcp.calls) == 1
    assert not repo.repo.list(AgentProposal, run_id=run.id, kind="tool_action")
    assert repo.repo.find_one(Task, run_id=run.id, role="web_testing").state == "STOPPED"


def test_late_model_response_cannot_overwrite_new_lease(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, output=action()
    )
    original = llm.complete

    def reclaim_then_respond(*args):
        current = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
        current.worker_id = "new-owner"
        current.lease_id = "replacement-lease"
        repo.repo.update(current)
        return original(*args)

    llm.complete = reclaim_then_respond
    scheduler.tick("review-worker", limit=8)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    assert task.worker_id == "new-owner" and task.lease_id == "replacement-lease"
    assert not repo.repo.list(AgentProposal, run_id=run.id, kind="tool_action")


def test_turn_limit_prevents_unbounded_followups(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs,
        evidence_store,
        tool_runner,
        engagement,
        repo,
        output=[action(), action("https://example.com/search?q=third")],
    )
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    task.iteration_budget = 2
    repo.repo.update(task)
    scheduler.tick("review-worker", limit=8)
    scheduler.tick("review-worker", limit=8)
    assert len(mcp.calls) == 2
    assert "turn budget" in repo.repo.get(Task, task.id).checkpoint["stop_reason"]


def test_uncertain_inflight_tool_is_not_replayed_on_restart(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(base_kwargs, evidence_store, tool_runner, engagement, repo)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    task.checkpoint = {"action_in_flight": True}
    repo.repo.update(task)
    scheduler.tick("review-worker", limit=8)
    assert not mcp.calls
    assert "uncertain" in repo.repo.get(Task, task.id).checkpoint["stop_reason"]


def test_timeout_cannot_become_a_passing_test(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(
        base_kwargs, evidence_store, tool_runner, engagement, repo, output=final()
    )
    mcp.call_tool = lambda *args: {"result": {"outcome": "TIMEOUT"}}
    scheduler.tick("review-worker", limit=8)
    assert repo.repo.find_one(CoverageRecord, run_id=run.id).status == "INCONCLUSIVE"


def test_legacy_tool_action_field_is_rejected_instead_of_ignored():
    from pentest_platform.domain.agents import validate_agent_output
    from pentest_platform.domain.errors import ValidationError

    with pytest.raises(ValidationError):
        validate_agent_output(
            "web_testing", {"candidates": [], "coverage_status": "INCONCLUSIVE", "tool_actions": []}
        )


def test_followup_evidence_reopens_inconclusive_candidate(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    run, executor, scheduler, llm, mcp = start(base_kwargs, evidence_store, tool_runner, engagement, repo)
    finding = Finding(
        id="reopen",
        engagement_id=engagement.id,
        run_id=run.id,
        title="Comparison",
        state="INCONCLUSIVE",
        version=2,
    )
    repo.repo.add(finding)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    task.input_records = {"follow_up_finding_id": finding.id}
    with executor.uow_factory() as uow:
        ok, _, reopened = executor._apply_candidate(
            uow,
            SimpleNamespace(),
            run,
            engagement,
            task,
            repo.repo.get(Scenario, task.scenario_id),
            {"title": "Comparison", "actual": "New comparison evidence", "assets": ["example.com"]},
            "evidence/new",
            "digest",
        )
        assert ok and reopened.state == "CANDIDATE" and reopened.version == 3
        executor._schedule_validation(uow, run, engagement, reopened)
        ok, _ = executor._apply_validation(
            uow,
            SimpleNamespace(),
            run,
            engagement,
            SimpleNamespace(input_records={"expected_version": 3}),
            {"verdict": "VALIDATED", "rationale": "New evidence supports the result"},
            finding.id,
        )
        assert ok
    assert repo.repo.get(Finding, finding.id).state == "VALIDATED"


def test_startup_preserves_admin_release_and_suggests_drafts(repo, clock, ids, active_release):
    from pentest_platform.bootstrap.seed import _ensure_agent_prompts
    from pentest_platform.domain.entities import PromptRelease, SystemPrompt

    with repo as uow:
        _ensure_agent_prompts(uow, clock, ids)
        _ensure_agent_prompts(uow, clock, ids)
    assert repo.repo.find_one(PromptRelease, state="ACTIVE").id == active_release.id
    assert len(repo.repo.list(SystemPrompt, state="DRAFT")) == 8


def test_stop_confirmation_waits_for_active_tool_acknowledgment(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, clock
):
    from datetime import timedelta

    run, executor, scheduler, llm, mcp = start(base_kwargs, evidence_store, tool_runner, engagement, repo)
    current = repo.repo.get(Run, run.id)
    current.state = "STOPPING"
    repo.repo.update(current)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    task.state = "RUNNING"
    task.authority_expires_at = clock.now() + timedelta(seconds=60)
    repo.repo.update(task)
    scheduler.finalize()
    assert repo.repo.get(Run, run.id).state == "STOPPING"
    task.state = "STOPPED"
    repo.repo.update(task)
    scheduler.finalize()
    assert repo.repo.get(Run, run.id).state == "STOPPED"


def test_unconfirmed_stop_is_failure_not_false_confirmation(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, clock
):
    from datetime import timedelta

    run, executor, scheduler, llm, mcp = start(base_kwargs, evidence_store, tool_runner, engagement, repo)
    current = repo.repo.get(Run, run.id)
    current.state = "STOPPING"
    repo.repo.update(current)
    task = repo.repo.find_one(Task, run_id=run.id, role="web_testing")
    task.state = "RUNNING"
    task.authority_expires_at = clock.now() - timedelta(seconds=1)
    repo.repo.update(task)
    scheduler.finalize()
    assert repo.repo.get(Run, run.id).state == "FAILED"
    assert "reconciliation" in repo.repo.get(Run, run.id).reason
