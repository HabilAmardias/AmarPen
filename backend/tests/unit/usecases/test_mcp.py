from datetime import timedelta

import pytest

from pentest_platform.adapters.mcp.authority import HmacMcpAuthority
from pentest_platform.domain.entities import (
    McpExecutionAuthority,
    McpScanJob,
    McpServer,
    McpToolManifest,
    Run,
    Task,
)
from pentest_platform.domain.errors import ConflictError, ForbiddenError
from pentest_platform.usecases.mcp import McpUsecase
from tests.fakes import FakeMcpHost, actor


def make_mcp(base_kwargs, evidence_store, tool_runner):
    host = FakeMcpHost(tool_runner)
    return McpUsecase(
        **base_kwargs,
        mcp_host=host,
        authority=HmacMcpAuthority("secret"),
        tool_runner=tool_runner,
        evidence_store=evidence_store,
        enabled=True,
        server_stable_id="local-mcp",
        protocol_revision="2026-07-28",
        sdk_version="2.3.0",
    )


def add_baseline(repo, clock, ids):
    repo.repo.add(
        McpServer(
            id=ids.new_id(),
            stable_id="local-mcp",
            endpoint="https://mcp-server:8443/mcp",
            implementation_version="2.3.0",
            protocol_revision="2026-07-28",
            enabled=True,
            created_at=clock.now(),
            updated_at=clock.now(),
        )
    )
    tools = [
        {"name": "http_probe", "inputSchema": {"type": "object"}, "allowed_roles": ["web_testing", "discovery"]},
        {"name": "scan_start", "inputSchema": {"type": "object"}, "allowed_roles": ["web_testing"]},
        {"name": "scan_status", "inputSchema": {"type": "object"}, "allowed_roles": ["web_testing"]},
        {"name": "scan_cancel", "inputSchema": {"type": "object"}, "allowed_roles": ["web_testing"]},
    ]
    repo.repo.add(
        McpToolManifest(
            id=ids.new_id(),
            server_id="local-mcp",
            version=1,
            tools=tools,
            integrity_hash="hash",
            state="ACTIVE",
            validation_detail={"passed": True, "tools_present": True, "unique_names": True, "schemas_present": True, "hash_present": True},
            validated_at=clock.now(),
            validated_by="system",
            created_at=clock.now(),
        )
    )


def test_mcp_readiness_and_pin(base_kwargs, repo, clock, ids, evidence_store, tool_runner):
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    assert usecase.ready()["ready"] is False
    add_baseline(repo, clock, ids)
    assert usecase.ready()["ready"] is True
    pin = usecase.pin_for_run()
    assert pin["server_id"] == "local-mcp"
    assert pin["manifest_hash"] == "hash"


def test_mcp_http_probe_and_authority(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    result = usecase.invoke(token, "http_probe", {"target": "example.com"})
    assert result["state"] == "COMPLETED"
    assert result["result"]["outcome"] == "COMPLETED"


def test_mcp_paused_run_is_denied(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="PAUSED", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    with pytest.raises(ForbiddenError):
        usecase.invoke(token, "http_probe", {"target": "example.com"})


def test_mcp_scan_job_is_durable(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "scan_start", "web_testing")
        uow.commit()
    started = usecase.invoke(token, "scan_start", {"scan_tool": "http", "target": "example.com"})
    assert started["state"] == "QUEUED"
    processed = usecase.process_jobs("worker-1")
    assert processed[0].state == "COMPLETED"


def test_mcp_discovery_creates_draft_manifest(base_kwargs, repo, clock, ids, evidence_store, tool_runner):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    manifest = usecase.discover(actor(), "local-mcp")
    assert manifest.state == "DRAFT"
    activated = usecase.activate_manifest(actor(), manifest.id)
    assert activated.state == "ACTIVE"


def test_mcp_disabled_state(base_kwargs, evidence_store, tool_runner):
    usecase = McpUsecase(
        **base_kwargs,
        mcp_host=FakeMcpHost(tool_runner),
        authority=HmacMcpAuthority("secret"),
        tool_runner=tool_runner,
        evidence_store=evidence_store,
        enabled=False,
        server_stable_id="local-mcp",
        protocol_revision="2026-07-28",
        sdk_version="2.3.0",
    )
    assert usecase.ready()["ready"] is False
    with pytest.raises(ConflictError):
        usecase.pin_for_run()


def test_mcp_tool_binding_is_enforced(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    with pytest.raises(ForbiddenError):
        usecase.invoke(token, "scan_start", {"target": "example.com"})


def test_mcp_scan_status_and_cancel(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    with usecase.uow_factory() as uow:
        start_token = usecase.issue_authority(uow, run, task, engagement, "scan_start", "web_testing")
        uow.commit()
    started = usecase.invoke(start_token, "scan_start", {"scan_tool": "http", "target": "example.com"})
    with usecase.uow_factory() as uow:
        status_token = usecase.issue_authority(uow, run, task, engagement, "scan_status", "web_testing")
        cancel_token = usecase.issue_authority(uow, run, task, engagement, "scan_cancel", "web_testing")
        uow.commit()
    status = usecase.invoke(status_token, "scan_status", {"execution_id": started["execution_id"]})
    assert status["state"] == "QUEUED"
    cancelled = usecase.invoke(cancel_token, "scan_cancel", {"execution_id": started["execution_id"]})
    assert cancelled["state"] == "CANCELLED"


def test_mcp_disabled_server_blocks_readiness(base_kwargs, repo, clock, ids, evidence_store, tool_runner):
    add_baseline(repo, clock, ids)
    server = repo.repo.find_one(McpServer, stable_id="local-mcp")
    server.enabled = False
    repo.repo.update(server)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    assert usecase.ready()["ready"] is False


def test_mcp_registry_lifecycle(base_kwargs, repo, clock, ids, evidence_store, tool_runner):
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    server = usecase.create_server(actor(), {"stable_id": "new-mcp", "endpoint": "https://mcp-server:8443/mcp", "protocol_revision": "2026-07-28"})
    assert server.enabled is True
    updated = usecase.update_server(actor(), "new-mcp", {"endpoint": "https://mcp2:8443/mcp"})
    assert updated.endpoint.endswith("mcp2:8443/mcp")
    revoked = usecase.revoke_server(actor(), "new-mcp", "test")
    assert revoked.enabled is False and revoked.revoked_reason == "test"


def test_mcp_manifest_validation_and_revocation_pauses_runs(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    add_baseline(repo, clock, ids)
    manifest = usecase.discover(actor(), "local-mcp")
    validated = usecase.validate_manifest(actor(), manifest.id)
    assert validated.validation_detail["passed"] is True
    active = usecase.activate_manifest(actor(), manifest.id)
    run = Run(
        id=ids.new_id(),
        engagement_id=engagement.id,
        state="RUNNING",
        initiated_by="user-1",
        config_snapshot={"mcp": {"server_id": "local-mcp", "manifest_id": active.id, "manifest_hash": active.integrity_hash}},
    )
    repo.repo.add(run)
    usecase.revoke_manifest(actor(), active.id, "compromised manifest")
    assert repo.repo.get(Run, run.id).state == "PAUSING"


def test_mcp_authority_replay_is_denied(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    usecase.invoke(token, "http_probe", {"target": "example.com"})
    with pytest.raises(ForbiddenError):
        usecase.invoke(token, "http_probe", {"target": "example.com"})


def test_mcp_lock_contention_is_denied(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    from pentest_platform.domain.entities import ResourceLock

    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    repo.repo.add(ResourceLock(id=ids.new_id(), run_id=run.id, lock_key="state-change:example.com", owner_task_id="other", state="HELD", acquired_at=clock.now(), expires_at=clock.now() + __import__("datetime").timedelta(seconds=60)))
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    with pytest.raises(ForbiddenError):
        usecase.invoke(token, "http_probe", {"target": "example.com"})


def test_scan_worker_claim_execute_and_cancel(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "scan_start", "web_testing")
        uow.commit()
    started = usecase.invoke(token, "scan_start", {"scan_tool": "http", "target": "example.com", "idempotency_key": "scan-1"})
    with usecase.uow_factory() as uow:
        retry_token = usecase.issue_authority(uow, run, task, engagement, "scan_start", "web_testing")
        uow.commit()
    duplicate = usecase.invoke(retry_token, "scan_start", {"scan_tool": "http", "target": "example.com", "idempotency_key": "scan-1"})
    assert started["execution_id"] == duplicate["execution_id"]
    claim_token = token
    job = repo.repo.find_one(McpScanJob, execution_id=started["execution_id"])
    job.authority_token = claim_token
    repo.repo.update(job)
    claimed = usecase.claim_jobs("scan-worker", limit=1)
    assert claimed and claimed[0].state == "RUNNING"
    executed = usecase.execute_job(claimed[0].id, "scan-worker")
    assert executed is not None and executed.state in {"COMPLETED", "FAILED"}


def test_mcp_manifest_validation_rejects_duplicate_tools(base_kwargs, repo, clock, ids, evidence_store, tool_runner):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    manifest = None
    with usecase.uow_factory() as uow:
        server = uow.repo.find_one(McpServer, stable_id="local-mcp")
        manifest = McpToolManifest(
            id=ids.new_id(),
            server_id=server.stable_id,
            tools=[{"name": "same", "inputSchema": {}, "allowed_roles": ["web_testing"]}, {"name": "same", "inputSchema": {}, "allowed_roles": ["web_testing"]}],
            integrity_hash="hash",
            created_at=clock.now(),
        )
        uow.repo.add(manifest)
        uow.commit()
    validated = usecase.validate_manifest(actor(), manifest.id)
    assert validated.validation_detail["passed"] is False


def test_mcp_revoke_server_pauses_pinned_run(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(
        id=ids.new_id(),
        engagement_id=engagement.id,
        state="RUNNING",
        initiated_by="user-1",
        config_snapshot={"mcp": {"server_id": "local-mcp", "manifest_id": "manifest-x"}},
    )
    repo.repo.add(run)
    usecase.revoke_server(actor(), "local-mcp", "server compromised")
    assert repo.repo.get(Run, run.id).state == "PAUSING"


def test_mcp_budget_and_revoked_manifest_are_denied(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    from pentest_platform.domain.entities import BudgetLedger

    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    repo.repo.add(BudgetLedger(id=ids.new_id(), run_id=run.id, request_limit=0, request_used=1, model_limit=10, iteration_limit=10, task_limit=10))
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    with pytest.raises(ForbiddenError):
        usecase.invoke(token, "http_probe", {"target": "example.com"})
    with usecase.uow_factory() as uow:
        manifest = uow.repo.find_one(McpToolManifest, server_id="local-mcp", state="ACTIVE")
        manifest.state = "REVOKED"
        uow.repo.update(manifest)
        token2 = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    with pytest.raises(ForbiddenError):
        usecase.invoke(token2, "http_probe", {"target": "example.com"})


def test_mcp_expired_authority_is_denied(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):

    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role="web_testing", state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        authority = uow.repo.find_one(McpExecutionAuthority, run_id=run.id)
        authority.expires_at = clock.now() - timedelta(seconds=1)
        uow.repo.update(authority)
        uow.commit()
    with pytest.raises(ForbiddenError):
        usecase.invoke(token, "http_probe", {"target": "example.com"})


class StubCrawler:
    def map(self, payload, request_guard=None):
        return {"endpoints": [{"url": "https://example.com/health", "methods": ["GET"]}], "count": 1, "requests": 1, "errors": [], "truncated": False}


class StubRequestRunner:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def run(self, target, method="GET", **kwargs):
        return {"outcome": "COMPLETED", "method": method, "target": target, "status_code": self.status_code, "headers": {}, "bytes": 2, "body_hash": "hash", "body_preview": "{}", "duration_ms": 1}


class StubIdentityService:
    def identity_for_run(self, uow, run_id, identity_id):
        return {}, {"session": "cookie"}


def _run_task(repo, ids, engagement, role="discovery"):
    run = Run(id=ids.new_id(), engagement_id=engagement.id, state="RUNNING", initiated_by="user-1")
    task = Task(id=ids.new_id(), run_id=run.id, scenario_id="", role=role, state="RUNNING", asset="example.com")
    repo.repo.add(run)
    repo.repo.add(task)
    return run, task


def test_mcp_map_and_request_tools(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    manifest = repo.repo.find_one(McpToolManifest, server_id="local-mcp", state="ACTIVE")
    manifest.tools.extend(
        [
            {"name": "map_endpoints", "inputSchema": {"type": "object"}, "allowed_roles": ["discovery"]},
            {"name": "http_request", "inputSchema": {"type": "object"}, "allowed_roles": ["discovery", "web_testing"]},
        ]
    )
    repo.repo.update(manifest)
    usecase = McpUsecase(
        **base_kwargs,
        mcp_host=FakeMcpHost(tool_runner),
        authority=HmacMcpAuthority("secret"),
        tool_runner=tool_runner,
        evidence_store=evidence_store,
        enabled=True,
        server_stable_id="local-mcp",
        protocol_revision="2026-07-28",
        sdk_version="2.3.0",
        endpoint_crawler=StubCrawler(),
        request_runner=StubRequestRunner(200),
        identity_service=StubIdentityService(),
    )
    run, task = _run_task(repo, ids, engagement)
    with usecase.uow_factory() as uow:
        map_token = usecase.issue_authority(uow, run, task, engagement, "map_endpoints", "discovery")
        req_token = usecase.issue_authority(uow, run, task, engagement, "http_request", "discovery")
        uow.commit()
    mapped = usecase.invoke(map_token, "map_endpoints", {"target": "example.com"})
    assert mapped["result"]["count"] == 1
    requested = usecase.invoke(req_token, "http_request", {"target": "https://example.com/health", "method": "GET", "identity_id": "identity-1"})
    assert requested["result"]["status_code"] == 200


def test_mcp_budget_at_limit_blocks_network_before_execution(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    from pentest_platform.domain.entities import BudgetLedger
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run, task = _run_task(repo, ids, engagement, "web_testing")
    repo.repo.add(BudgetLedger(id=ids.new_id(), run_id=run.id, request_limit=1, request_used=1))
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    with pytest.raises(ForbiddenError, match="budget"):
        usecase.invoke(token, "http_probe", {"target": "example.com"})
    assert not tool_runner.calls


def test_mcp_reclaimed_lease_rejects_old_authority(base_kwargs, repo, clock, ids, evidence_store, tool_runner, engagement):
    add_baseline(repo, clock, ids)
    usecase = make_mcp(base_kwargs, evidence_store, tool_runner)
    run, task = _run_task(repo, ids, engagement, "web_testing")
    task.lease_id = "old-lease"
    repo.repo.update(task)
    with usecase.uow_factory() as uow:
        token = usecase.issue_authority(uow, run, task, engagement, "http_probe", "web_testing")
        uow.commit()
    task.lease_id = "new-lease"
    repo.repo.update(task)
    with pytest.raises(ForbiddenError, match="lease"):
        usecase.invoke(token, "http_probe", {"target": "example.com"})
    assert not tool_runner.calls
