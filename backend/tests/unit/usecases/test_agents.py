import pytest

from pentest_platform.domain.agents import ProposalStatus, validate_agent_output
from pentest_platform.domain.entities import (
    AgentProposal,
    Assessment,
    Finding,
    ReportSnapshot,
    Run,
    Scenario,
    Task,
)
from pentest_platform.domain.errors import ValidationError
from pentest_platform.usecases.agent_runtime import AgentExecutionUsecase
from pentest_platform.usecases.agent_scheduler import AgentSchedulerUsecase
from pentest_platform.usecases.findings import FindingUsecase
from pentest_platform.usecases.runs import RunUsecase
from tests.fakes import FakeLlmGateway, actor


def make_scheduler(base_kwargs, evidence_store, tool_runner, llm):
    executor = AgentExecutionUsecase(
        **base_kwargs,
        llm_gateway=llm,
        evidence_store=evidence_store,
        tool_runner=tool_runner,
    )
    return AgentSchedulerUsecase(**base_kwargs, executor=executor)


def run_until_complete(scheduler, run_id, repo, attempts=12):
    for _ in range(attempts):
        scheduler.tick("worker-1", limit=8)
        if repo.repo.get(Run, run_id).state in {"COMPLETED", "FAILED", "STOPPED", "PAUSED"}:
            return repo.repo.get(Run, run_id)
    return repo.repo.get(Run, run_id)


def test_agent_contracts_reject_invalid_output():
    with pytest.raises(ValidationError):
        validate_agent_output("orchestrator", {"tasks": [{"role": "not_a_role"}]})
    validate_agent_output("orchestrator", {"tasks": []})


def test_orchestrator_scope_escape_is_denied(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    llm = FakeLlmGateway(
        responses={
            "orchestrator": {
                "tasks": [
                    {
                        "role": "web_testing",
                        "kind": "test",
                        "scenario_key": "WSTG-INPV-01",
                        "asset": "outside.example.net",
                        "reason": "scope escape",
                    }
                ]
            }
        }
    )
    scenario = Scenario(id="scenario-xss", key="WSTG-INPV-01", version="1.0", title="XSS", agent_role="web_testing")
    repo.repo.add(scenario)
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, llm)
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "scope-1")
    scheduler.tick("worker-1", limit=2)
    proposals = repo.repo.list(AgentProposal, run_id=run.id)
    assert proposals[0].status == ProposalStatus.DENIED
    assert not [task for task in repo.repo.list(Task, run_id=run.id) if task.asset == "outside.example.net"]


def test_handoff_pipeline_reaches_validated_risk_and_report(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, ids
):
    scenario = Scenario(
        id=ids.new_id(),
        key="WSTG-INPV-01",
        version="1.0",
        title="Cross-site scripting",
        agent_role="web_testing",
        framework_refs=["WSTG-INPV-01"],
        side_effects=["read_only"],
    )
    repo.repo.add(scenario)
    llm = FakeLlmGateway(
        responses={
            "orchestrator": {
                "tasks": [
                    {
                        "role": "discovery",
                        "kind": "discovery",
                        "scenario_key": "WSTG-INFO-01",
                        "asset": "example.com",
                        "reason": "discover",
                        "depends_on": [],
                    },
                    {
                        "role": "web_testing",
                        "kind": "test",
                        "scenario_key": "WSTG-INPV-01",
                        "asset": "example.com",
                        "reason": "test",
                        "depends_on": ["discovery:wstg-info-01:example.com"],
                    },
                ]
            },
            "discovery": {"assets": [{"kind": "target", "value": "example.com"}]},
            "web_testing": {
                "candidates": [
                    {
                        "title": "Reflected XSS",
                        "actual": "payload reflected",
                        "assets": ["example.com"],
                        "expected": "output encoded",
                    }
                ],
                "coverage_status": "TESTED_ISSUE_CONFIRMED",
            },
            "validation": {"verdict": "VALIDATED", "rationale": "Reproduced with evidence"},
        }
    )
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, llm)
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "flow-1")
    completed = run_until_complete(scheduler, run.id, repo)
    assert completed.state == "COMPLETED"
    finding = repo.repo.list(Finding, engagement_id=engagement.id)[0]
    assert finding.state == "VALIDATED"
    assert repo.repo.find_one(Assessment, finding_id=finding.id) is not None
    report = repo.repo.list(ReportSnapshot, engagement_id=engagement.id)[0]
    assert report.status == "PREVIEW"
    roles = {task.role for task in repo.repo.list(Task, run_id=run.id)}
    assert {"orchestrator", "discovery", "web_testing", "validation", "risk_assessment", "reporting"} <= roles


def test_paused_run_cannot_execute_claimed_task(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    llm = FakeLlmGateway()
    executor = AgentExecutionUsecase(**base_kwargs, llm_gateway=llm, evidence_store=evidence_store, tool_runner=tool_runner)
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "paused-1")
    task = repo.repo.list(Task, run_id=run.id)[0]
    task.state = "RUNNING"
    task.worker_id = "worker-1"
    task.lease_id = "lease-1"
    repo.repo.update(task)
    stored = repo.repo.get(Run, run.id)
    stored.state = "PAUSED"
    repo.repo.update(stored)
    executor.execute_task(task.id, "worker-1")
    stored_task = repo.repo.get(Task, task.id)
    assert stored_task.outcome == "STALE"
    assert stored_task.state == "PAUSED"
    assert not llm.calls


def test_budget_exhaustion_pauses_run(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    engagement.budgets = {"max_model_calls": 0, "max_requests": 10, "max_tasks": 10, "max_iterations": 5}
    repo.repo.update(engagement)
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, FakeLlmGateway())
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "budget-1")
    scheduler.tick("worker-1")
    stored = repo.repo.get(Run, run.id)
    assert stored.state in {"PAUSING", "PAUSED"}
    assert repo.repo.list(Task, run_id=run.id)[0].outcome == "BUDGET_EXHAUSTED"


def test_retest_orchestrator_cannot_expand_to_full_catalogue(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, ids
):
    selected = Scenario(id=ids.new_id(), key="WSTG-ATHZ-02", version="1.0", title="IDOR", agent_role="authorization_business_logic")
    other = Scenario(id=ids.new_id(), key="WSTG-INPV-01", version="1.0", title="XSS", agent_role="web_testing")
    repo.repo.add(selected)
    repo.repo.add(other)
    finding = Finding(
        id=ids.new_id(),
        engagement_id=engagement.id,
        run_id="original-run",
        title="IDOR",
        affected_assets=["example.com"],
        scenario_id=selected.id,
        scenario_version="1.0",
        state="VALIDATED",
    )
    repo.repo.add(finding)
    findings = FindingUsecase(**base_kwargs, evidence_store=evidence_store)
    attempt = findings.start_retest(actor(), engagement.id, [finding.id], "retest", "retest-1")
    llm = FakeLlmGateway(
        responses={
            "orchestrator": {
                "tasks": [
                    {
                        "role": "web_testing",
                        "kind": "test",
                        "scenario_key": "WSTG-INPV-01",
                        "asset": "example.com",
                        "reason": "wrong scenario",
                    }
                ]
            }
        }
    )
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, llm)
    scheduler.tick("worker-1")
    proposals = [p for p in repo.repo.list(AgentProposal, run_id=attempt.run_id)]
    assert proposals[0].status == ProposalStatus.DENIED
    assert not [task for task in repo.repo.list(Task, run_id=attempt.run_id) if task.role == "web_testing"]


def test_invalid_agent_output_is_bounded(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, clock):
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, FakeLlmGateway(invalid=True))
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "invalid-1")
    for _ in range(6):
        scheduler.tick("worker-1")
        clock.advance(seconds=10)
    tasks = repo.repo.list(Task, run_id=run.id)
    assert any(task.outcome == "INVALID_OUTPUT" for task in tasks)
    assert any(task.state == "FAILED" for task in tasks)


def test_orchestrator_cannot_directly_schedule_agent_managed_role(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    scheduler = make_scheduler(
        base_kwargs,
        evidence_store,
        tool_runner,
        FakeLlmGateway(
            responses={
                "orchestrator": {
                    "tasks": [
                        {"role": "validation", "kind": "validation", "asset": "example.com", "reason": "direct"}
                    ]
                }
            }
        ),
    )
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "direct-1")
    scheduler.tick("worker-1")
    proposals = repo.repo.list(AgentProposal, run_id=run.id)
    assert proposals[0].status == "DENIED"
    assert not [task for task in repo.repo.list(Task, run_id=run.id) if task.role == "validation"]


def test_discovery_asset_outside_scope_is_denied(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    scheduler = make_scheduler(
        base_kwargs,
        evidence_store,
        tool_runner,
        FakeLlmGateway(
            responses={
                "orchestrator": {
                    "tasks": [
                        {"role": "discovery", "kind": "discovery", "asset": "example.com", "reason": "discover"}
                    ]
                },
                "discovery": {"assets": [{"kind": "endpoint", "value": "https://outside.example.net/admin"}]},
            }
        ),
    )
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "asset-1")
    scheduler.tick("worker-1")
    scheduler.tick("worker-1")
    proposals = repo.repo.list(AgentProposal, run_id=run.id)
    assert any(proposal.kind == "record_assets" and proposal.status == "DENIED" for proposal in proposals)


def test_tool_failure_produces_explicit_outcome(
    base_kwargs, evidence_store, engagement, active_release, repo
):
    class BrokenRunner:
        def available(self, tool):
            return True

        def run(self, tool, parameters, *, timeout=60):
            raise RuntimeError("tool failed")

    scheduler = make_scheduler(base_kwargs, evidence_store, BrokenRunner(), FakeLlmGateway())
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=BrokenRunner()).start(actor(), engagement.id, "tool-1")
    scheduler.tick("worker-1")
    scheduler.tick("worker-1")
    discovery = [task for task in repo.repo.list(Task, run_id=run.id) if task.role == "discovery"][0]
    assert discovery.outcome == "INCONCLUSIVE"


def test_invalid_risk_inputs_are_denied(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, ids
):
    scenario = Scenario(id=ids.new_id(), key="WSTG-INPV-01", version="1.0", title="XSS", agent_role="web_testing", side_effects=["read_only"])
    repo.repo.add(scenario)
    llm = FakeLlmGateway(
        responses={
            "orchestrator": {
                "tasks": [
                    {"role": "discovery", "kind": "discovery", "asset": "example.com", "reason": "discover"},
                    {"role": "web_testing", "kind": "test", "scenario_key": "WSTG-INPV-01", "asset": "example.com", "reason": "test"},
                ]
            },
            "discovery": {"assets": [{"kind": "target", "value": "example.com"}]},
            "web_testing": {
                "candidates": [{"title": "XSS", "actual": "reflected", "assets": ["example.com"]}],
                "coverage_status": "TESTED_ISSUE_CONFIRMED",
            },
            "validation": {"verdict": "VALIDATED", "rationale": "evidence"},
            "risk_assessment": {
                "cvss_vector": "not-a-vector",
                "cvss_rationale": {},
                "business_likelihood": 4,
                "business_impact": 4,
                "business_rationale": "impact",
                "confidence": "high",
            },
        }
    )
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, llm)
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "risk-1")
    for _ in range(8):
        scheduler.tick("worker-1", limit=8)
    proposals = repo.repo.list(AgentProposal, run_id=run.id)
    assert any(proposal.kind == "risk_inputs" and proposal.status == "DENIED" for proposal in proposals)


def test_scheduler_pauses_and_stops_runs(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo
):
    llm = FakeLlmGateway()
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, llm)
    run_usecase = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner)
    paused_run = run_usecase.start(actor(), engagement.id, "pause-sched-1")
    stored = repo.repo.get(Run, paused_run.id)
    stored.state = "PAUSING"
    repo.repo.update(stored)
    scheduler.finalize()
    assert repo.repo.get(Run, paused_run.id).state == "PAUSED"
    paused = repo.repo.get(Run, paused_run.id)
    paused.state = "STOPPED"
    repo.repo.update(paused)
    stopped_run = run_usecase.start(actor(), engagement.id, "stop-sched-1")
    stored = repo.repo.get(Run, stopped_run.id)
    stored.state = "STOPPING"
    repo.repo.update(stored)
    scheduler.finalize()
    assert repo.repo.get(Run, stopped_run.id).state == "STOPPED"


def test_expired_lease_is_recovered(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo):
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, FakeLlmGateway())
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "lease-1")
    task = repo.repo.list(Task, run_id=run.id)[0]
    task.state = "RUNNING"
    task.attempt = 1
    from datetime import timedelta

    task.authority_expires_at = scheduler.clock.now() - timedelta(seconds=5)
    repo.repo.update(task)
    scheduler.claim_batch("worker-1")
    scheduler.clock.advance(seconds=20)
    scheduler.claim_batch("worker-1")
    assert repo.repo.get(Task, task.id).attempt >= 2


def test_unknown_role_proposal_is_denied(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo):
    scheduler = make_scheduler(
        base_kwargs,
        evidence_store,
        tool_runner,
        FakeLlmGateway(responses={"orchestrator": {"tasks": [{"role": "unknown_role", "kind": "test", "reason": "bad"}]}}),
    )
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "unknown-1")
    scheduler.tick("worker-1")
    assert not repo.repo.list(AgentProposal, run_id=run.id)
    assert any(task.outcome == "INVALID_OUTPUT" for task in repo.repo.list(Task, run_id=run.id))


def test_validation_without_evidence_is_inconclusive(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, ids
):
    finding = Finding(
        id=ids.new_id(),
        engagement_id=engagement.id,
        run_id="run-old",
        title="No evidence",
        affected_assets=["example.com"],
        state="CANDIDATE",
    )
    repo.repo.add(finding)
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "nov-1")
    orchestrator = repo.repo.list(Task, run_id=run.id)[0]
    orchestrator.state = "COMPLETED"
    repo.repo.update(orchestrator)
    validation_task = Task(
        id=ids.new_id(),
        run_id=run.id,
        scenario_id="",
        state="QUEUED",
        role="validation",
        kind="validation",
        asset="example.com",
        ownership_key="validation:no-evidence",
        input_records={"finding_id": finding.id, "expected_version": finding.version},
        prompt_release_id=active_release.id,
        model_profile=engagement.model_profile,
    )
    repo.repo.add(validation_task)
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, FakeLlmGateway())
    scheduler.tick("worker-1")
    assert repo.repo.get(Finding, finding.id).state == "INCONCLUSIVE"


def test_state_changing_task_waits_for_lock(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, ids, clock):
    from pentest_platform.domain.entities import ResourceLock

    scenario = Scenario(id=ids.new_id(), key="WSTG-BUSL-01", version="1.0", title="Flow", agent_role="authorization_business_logic", side_effects=["state_change"])
    repo.repo.add(scenario)
    run = RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner).start(actor(), engagement.id, "lock-1")
    repo.repo.add(
        ResourceLock(
            id=ids.new_id(),
            run_id=run.id,
            lock_key="state-change:example.com",
            owner_task_id="other-task",
            state="HELD",
            acquired_at=clock.now(),
            expires_at=clock.now() + __import__("datetime").timedelta(seconds=60),
        )
    )
    orchestrator = repo.repo.list(Task, run_id=run.id)[0]
    orchestrator.state = "COMPLETED"
    repo.repo.update(orchestrator)
    task = Task(
        id=ids.new_id(),
        run_id=run.id,
        scenario_id=scenario.id,
        state="QUEUED",
        role="authorization_business_logic",
        kind="test",
        asset="example.com",
        ownership_key="authorization_business_logic:WSTG-BUSL-01:example.com",
        prompt_release_id=active_release.id,
        model_profile=engagement.model_profile,
    )
    repo.repo.add(task)
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, FakeLlmGateway())
    scheduler.tick("worker-1")
    assert repo.repo.get(Task, task.id).checkpoint.get("waiting_lock") == "state-change:example.com"
