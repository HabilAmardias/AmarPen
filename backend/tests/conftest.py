import pytest

from pentest_platform.domain.entities import Engagement, ModelProfile, PromptRelease, RiskPolicy, SystemPrompt
from pentest_platform.domain.scoring import DEFAULT_BANDS, DEFAULT_MATRIX
from tests.fakes import (
    FakeAudit,
    FakeEvidenceStore,
    FakePasswordService,
    FakeReportRenderer,
    FakeToolRunner,
    FakeTotpService,
    FakeUnitOfWork,
    FixedClock,
    SequentialIds,
)


@pytest.fixture
def repo():
    return FakeUnitOfWork()


@pytest.fixture
def clock():
    return FixedClock()


@pytest.fixture
def ids():
    return SequentialIds()


@pytest.fixture
def audit(clock):
    return FakeAudit(clock)


@pytest.fixture
def uow_factory(repo):
    return lambda: repo


@pytest.fixture
def passwords():
    return FakePasswordService()


@pytest.fixture
def totp():
    return FakeTotpService()


@pytest.fixture
def evidence_store():
    return FakeEvidenceStore()


@pytest.fixture
def renderer():
    return FakeReportRenderer()


@pytest.fixture
def tool_runner():
    return FakeToolRunner()


@pytest.fixture
def base_kwargs(uow_factory, audit, clock, ids):
    return {"uow_factory": uow_factory, "audit": audit, "clock": clock, "ids": ids}


@pytest.fixture
def engagement(repo, ids):
    from pentest_platform.domain.entities import EngagementMember

    item = Engagement(
        id=ids.new_id(),
        name="Test Engagement",
        owner_id="user-1",
        authorization_ref="AUTH-1",
        authorization_valid=True,
        targets=["example.com"],
        exclusions=[],
        access_profile="anonymous",
        model_profile="local-default",
        business_context={"risk_owner": "owner"},
    )
    repo.repo.add(item)
    if repo.repo.find_one(ModelProfile, name="local-default") is None:
        repo.repo.add(
            ModelProfile(
                id="model-1",
                name="local-default",
                base_url="http://localhost:8080/v1",
                model="mock-pentest",
                capabilities=["chat", "structured_outputs"],
                last_test_status="REACHABLE",
                last_test_detail={"reachable": True, "chat_ok": True, "structured_outputs": True},
            )
        )
    repo.repo.add(
        EngagementMember(
            id=ids.new_id(),
            engagement_id=item.id,
            user_id="user-1",
            access_role="Analyst",
        )
    )
    return item


@pytest.fixture
def risk_policy(repo, ids, clock):
    policy = RiskPolicy(
        id=ids.new_id(),
        name="Test",
        version=1,
        active=True,
        matrix=DEFAULT_MATRIX,
        bands=DEFAULT_BANDS,
        created_at=clock.now(),
    )
    repo.repo.add(policy)
    return policy


@pytest.fixture
def active_release(repo, ids, clock):
    import hashlib

    from pentest_platform.domain.agents import AGENT_CONTRACTS

    manifest = {}
    for role, contract in AGENT_CONTRACTS.items():
        body = f"Act safely as {role}."
        prompt = SystemPrompt(
            id=ids.new_id(),
            key=contract.prompt_key,
            agent_role=str(role),
            purpose="test",
            state="PUBLISHED",
            version=1,
            body=body,
            content_hash=hashlib.sha256(body.encode()).hexdigest(),
            author_id="system",
            change_reason="test",
            created_at=clock.now(),
            published_at=clock.now(),
        )
        repo.repo.add(prompt)
        manifest[str(role)] = prompt.id
    release = PromptRelease(
        id=ids.new_id(),
        name="test-release",
        manifest=manifest,
        state="ACTIVE",
        version=1,
        validated=True,
        created_at=clock.now(),
    )
    repo.repo.add(release)
    return release
