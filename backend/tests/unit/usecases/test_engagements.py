import pytest

from pentest_platform.domain.entities import Engagement, Scenario
from pentest_platform.domain.errors import ConflictError, ForbiddenError, NotFoundError
from pentest_platform.usecases.engagements import EngagementUsecase
from tests.fakes import actor


def make_usecase(base_kwargs, evidence_store):
    return EngagementUsecase(**base_kwargs, evidence_store=evidence_store)


def test_create_engagement_requires_analyst(base_kwargs, evidence_store):
    usecase = make_usecase(base_kwargs, evidence_store)
    with pytest.raises(ForbiddenError):
        usecase.create_engagement(actor(roles=("Viewer",)), {"name": "Test"})
    created = usecase.create_engagement(
        actor(),
        {
            "name": "Test Engagement",
            "authorization_ref": "AUTH-1",
            "authorization_valid": True,
            "targets": ["Example.COM"],
            "exclusions": [],
        },
    )
    assert created.targets == ["example.com"]
    assert created.owner_id == "user-1"


def test_readiness_reports_blocking_failures(base_kwargs, evidence_store, engagement, repo):
    engagement.authorization_valid = False
    repo.repo.update(engagement)
    result = make_usecase(base_kwargs, evidence_store).readiness(actor(), engagement.id)
    assert result["ready"] is False
    assert "authorization" in result["blocking"]


def test_update_detects_version_conflict(base_kwargs, evidence_store, engagement):
    usecase = make_usecase(base_kwargs, evidence_store)
    with pytest.raises(ConflictError):
        usecase.update_engagement(actor(), engagement.id, {"name": "Renamed"}, expected_version=999)


def test_plan_skips_prohibited_side_effects(base_kwargs, evidence_store, engagement, repo, ids):
    engagement.prohibited = ["destructive_actions"]
    repo.repo.update(engagement)
    repo.repo.add(
        Scenario(
            id=ids.new_id(),
            key="WSTG-TEST",
            version="1.0",
            title="Test",
            side_effects=["destructive_actions"],
        )
    )
    result = make_usecase(base_kwargs, evidence_store).plan(actor(), engagement.id)
    assert result["skipped"][0]["scenario"] == "WSTG-TEST"


def test_cross_engagement_access_is_masked(base_kwargs, evidence_store, repo, ids):
    other = Engagement(
        id=ids.new_id(),
        name="Other",
        owner_id="someone-else",
        authorization_ref="AUTH-2",
        authorization_valid=True,
        targets=["other.example"],
    )
    repo.repo.add(other)
    with pytest.raises(NotFoundError):
        make_usecase(base_kwargs, evidence_store).get_engagement(actor(), other.id)
