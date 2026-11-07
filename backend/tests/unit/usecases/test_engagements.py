import pytest

from pentest_platform.domain.entities import Engagement, Scenario
from pentest_platform.domain.errors import ConflictError, ForbiddenError, NotFoundError
from pentest_platform.usecases.engagements import EngagementUsecase
from tests.fakes import actor


def make_usecase(base_kwargs, evidence_store):
    return EngagementUsecase(**base_kwargs, evidence_store=evidence_store)


def test_create_engagement_requires_analyst(base_kwargs, evidence_store, repo):
    from pentest_platform.domain.entities import ModelProfile

    repo.repo.add(
        ModelProfile(
            id="profile-1",
            name="local-default",
            base_url="http://localhost:8080/v1",
            model="mock",
            capabilities=["chat", "structured_outputs"],
            last_test_status="REACHABLE",
            last_test_detail={"reachable": True, "chat_ok": True, "structured_outputs": True},
        )
    )
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
            "model_profile": "local-default",
        },
    )
    assert created.targets == ["example.com"]
    assert created.owner_id == "user-1"


def test_model_profile_options_are_available_to_analysts(base_kwargs, evidence_store, engagement, repo):
    result = make_usecase(base_kwargs, evidence_store).model_profile_options(actor())
    assert result[0]["name"] == "local-default"
    assert "secret_ref" not in result[0]


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


def test_engagement_requires_an_enabled_model_profile(base_kwargs, evidence_store, repo):
    from pentest_platform.domain.errors import ValidationError

    usecase = make_usecase(base_kwargs, evidence_store)
    with pytest.raises(ValidationError):
        usecase.create_engagement(
            actor(),
            {
                "name": "No model",
                "authorization_ref": "AUTH-1",
                "authorization_valid": True,
                "targets": ["example.com"],
                "model_profile": "missing-profile",
            },
        )


def test_readiness_blocks_unverified_structured_output(base_kwargs, evidence_store, engagement, repo):
    from pentest_platform.domain.entities import ModelProfile

    profile = repo.repo.find_one(ModelProfile, name="local-default")
    profile.last_test_status = "REACHABLE"
    profile.last_test_detail = {"structured_outputs": False}
    repo.repo.update(profile)
    result = make_usecase(base_kwargs, evidence_store).readiness(actor(), engagement.id)
    assert result["ready"] is False
    assert "model_profile" in result["blocking"]
    message = next(check["message"] for check in result["checks"] if check["name"] == "model_profile")
    assert "structured-output" in message


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "ab", "authorization_ref": "AUTH-1", "targets": ["example.com"], "model_profile": "local-default"},
        {"name": "Valid", "authorization_ref": "AUTH-1", "targets": [], "model_profile": "local-default"},
        {"name": "Valid", "authorization_ref": "", "targets": ["example.com"], "model_profile": "local-default"},
        {"name": "Valid", "authorization_ref": "AUTH-1", "targets": ["example.com"], "model_profile": ""},
        {
            "name": "Valid",
            "authorization_ref": "AUTH-1",
            "targets": ["example.com"],
            "model_profile": "local-default",
            "window_start": "2026-01-02T00:00:00Z",
            "window_end": "2026-01-01T00:00:00Z",
        },
    ],
)
def test_create_engagement_validates_required_fields(base_kwargs, evidence_store, engagement, payload):
    from pentest_platform.domain.errors import ValidationError

    with pytest.raises(ValidationError):
        make_usecase(base_kwargs, evidence_store).create_engagement(actor(), payload)
