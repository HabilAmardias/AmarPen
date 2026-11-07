import pytest

from pentest_platform.domain.entities import AssetRecord, BudgetLedger, Run, Task
from pentest_platform.domain.errors import ConflictError
from pentest_platform.usecases.agent_runtime import AgentExecutionUsecase
from pentest_platform.usecases.agent_scheduler import AgentSchedulerUsecase
from pentest_platform.usecases.runs import RunUsecase
from tests.fakes import FakeLlmGateway, actor


def make_usecase(base_kwargs, evidence_store, tool_runner):
    return RunUsecase(**base_kwargs, evidence_store=evidence_store, tool_runner=tool_runner)


def make_scheduler(base_kwargs, evidence_store, tool_runner, llm):
    executor = AgentExecutionUsecase(
        **base_kwargs,
        llm_gateway=llm,
        evidence_store=evidence_store,
        tool_runner=tool_runner,
    )
    return AgentSchedulerUsecase(**base_kwargs, executor=executor)


def test_start_is_idempotent_and_creates_orchestrator_task(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo):
    usecase = make_usecase(base_kwargs, evidence_store, tool_runner)
    first = usecase.start(actor(), engagement.id, "idem-1")
    second = usecase.start(actor(), engagement.id, "idem-1")
    assert first.id == second.id
    tasks = repo.repo.list(Task, run_id=first.id)
    assert len(tasks) == 1
    assert tasks[0].role == "orchestrator"
    assert repo.repo.find_one(BudgetLedger, run_id=first.id) is not None


def test_start_requires_active_prompt_release(base_kwargs, evidence_store, tool_runner, engagement):
    usecase = make_usecase(base_kwargs, evidence_store, tool_runner)
    with pytest.raises(ConflictError):
        usecase.start(actor(), engagement.id, "idem-1")


def test_discovery_pipeline_records_assets_without_claiming_full_assessment(
    base_kwargs, evidence_store, tool_runner, engagement, active_release, repo, ids
):
    llm = FakeLlmGateway()
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, llm)
    run = make_usecase(base_kwargs, evidence_store, tool_runner).start(actor(), engagement.id, "idem-1")
    scheduler.tick("worker-1", limit=4)
    for _ in range(3):
        scheduler.tick("worker-1", limit=4)
    states = [task.role for task in repo.repo.list(Task, run_id=run.id)]
    assert "orchestrator" in states
    assert "discovery" in states
    assert "reporting" in states
    assert repo.repo.list(AssetRecord, run_id=run.id)
    assert repo.repo.get(Run, run.id).state == "FAILED"
    assert repo.repo.get(Run, run.id).config_snapshot["assessment_completeness"] == "PARTIAL"


def test_pause_resume_stop_controls(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo):
    usecase = make_usecase(base_kwargs, evidence_store, tool_runner)
    run = usecase.start(actor(), engagement.id, "start-1")
    stored = repo.repo.get(Run, run.id)
    stored.state = "RUNNING"
    repo.repo.update(stored)
    paused = usecase.pause(actor(), run.id, "pause-1")
    assert paused.state == "PAUSING"
    usecase.confirm_pause(run.id)
    assert repo.repo.get(Run, run.id).state == "PAUSED"
    resumed = usecase.resume(actor(), run.id, "resume-1")
    assert resumed.state == "RUNNING"
    stopped = usecase.stop(actor(), run.id, "stop-1", "done")
    assert stopped.state == "STOPPING"
    usecase.confirm_stop(run.id)
    assert repo.repo.get(Run, run.id).state == "STOPPED"
    with pytest.raises(ConflictError):
        usecase.resume(actor(), run.id, "resume-2")


def test_duplicate_commands_are_idempotent(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo):
    usecase = make_usecase(base_kwargs, evidence_store, tool_runner)
    run = usecase.start(actor(), engagement.id, "start-1")
    stored = repo.repo.get(Run, run.id)
    stored.state = "RUNNING"
    repo.repo.update(stored)
    first = usecase.pause(actor(), run.id, "pause-1")
    second = usecase.pause(actor(), run.id, "pause-1")
    assert first.id == second.id


def test_model_outage_pauses_run(base_kwargs, evidence_store, tool_runner, engagement, active_release, repo):
    llm = FakeLlmGateway(fail=True)
    scheduler = make_scheduler(base_kwargs, evidence_store, tool_runner, llm)
    run = make_usecase(base_kwargs, evidence_store, tool_runner).start(actor(), engagement.id, "idem-1")
    scheduler.tick("worker-1")
    stored = repo.repo.get(Run, run.id)
    assert stored.state in {"PAUSING", "PAUSED"}
    assert "model" in stored.reason.lower() or "model" in (stored.reason or "").lower() or stored.state == "PAUSED"
