from pentest_platform.domain.entities import AuthorizationAttestation, ModelProfile
from pentest_platform.usecases.engagements import EngagementUsecase
from tests.fakes import actor


def _profile() -> ModelProfile:
    return ModelProfile(
        id="model-1",
        name="ready",
        base_url="http://model/v1",
        model="mock",
        capabilities=["chat", "structured_outputs"],
        last_test_status="REACHABLE",
        last_test_detail={"structured_outputs": True},
    )


def test_quick_start_creates_engagement_and_attestation(base_kwargs, repo, evidence_store):
    repo.repo.add(_profile())
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    engagement = usecase.quick_start(
        actor(),
        {"base_url": "https://api.example.com/path", "authorization_attested": True},
        source_ip="127.0.0.1",
        user_agent="test-agent",
    )
    assert engagement.base_url == "https://api.example.com"
    assert engagement.targets == ["api.example.com"]
    assert engagement.authorization_valid is True
    assert engagement.authorization_ref.startswith("ATT-")
    assert engagement.window_end is not None
    assert engagement.budgets["max_requests"] == 500
    attestation = repo.repo.list(AuthorizationAttestation, engagement_id=engagement.id)[0]
    assert attestation.source_ip == "127.0.0.1"
    assert attestation.user_agent == "test-agent"
    status = usecase.authorization(actor(), engagement.id)
    assert status["valid"] is True


def test_quick_start_requires_attestation(base_kwargs, repo, evidence_store):
    import pytest

    from pentest_platform.domain.errors import ValidationError

    repo.repo.add(_profile())
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    with pytest.raises(ValidationError):
        usecase.quick_start(actor(), {"base_url": "https://example.com", "authorization_attested": False})


def test_scope_change_invalidates_attestation(base_kwargs, repo, evidence_store):
    repo.repo.add(_profile())
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    engagement = usecase.quick_start(
        actor(),
        {"base_url": "https://example.com", "authorization_attested": True},
    )
    usecase.update_engagement(
        actor(),
        engagement.id,
        {
            "targets": ["other.example.com"],
            "authorization_ref": engagement.authorization_ref,
            "authorization_valid": True,
            "model_profile": engagement.model_profile,
        },
        engagement.config_version,
    )
    status = usecase.authorization(actor(), engagement.id)
    assert status["valid"] is False
    assert "Authorization" in status["reason"]


def test_quick_start_requires_agent_ready_profile(base_kwargs, repo, evidence_store):
    import pytest

    from pentest_platform.domain.errors import ValidationError

    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    with pytest.raises(ValidationError):
        usecase.quick_start(actor(), {"base_url": "https://example.com", "authorization_attested": True})


def test_attestation_expires_after_window(base_kwargs, repo, evidence_store, clock):
    repo.repo.add(_profile())
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    engagement = usecase.quick_start(actor(), {"base_url": "https://example.com", "authorization_attested": True})
    clock.advance(hours=25)
    status = usecase.authorization(actor(), engagement.id)
    assert status["valid"] is False
    assert "expired" in status["reason"] or "ended" in status["reason"]


def test_legacy_authorization_record_remains_compatible(base_kwargs, repo, evidence_store):
    from pentest_platform.domain.entities import Engagement

    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    engagement = Engagement(
        id="legacy-1",
        name="Legacy",
        owner_id="user-1",
        authorization_ref="AUTH-1",
        authorization_valid=True,
        targets=["example.com"],
        model_profile="ready",
    )
    repo.repo.add(engagement)
    status = usecase.authorization(actor(), engagement.id)
    assert status["valid"] is True


def test_invalid_base_url_is_rejected(base_kwargs, evidence_store):
    import pytest

    from pentest_platform.domain.errors import ValidationError

    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    with pytest.raises(ValidationError):
        usecase.quick_start(actor(), {"base_url": "ftp://example.com", "authorization_attested": True})


def test_reattest_revokes_previous_attestation(base_kwargs, repo, evidence_store):
    from pentest_platform.domain.entities import AuthorizationAttestation

    repo.repo.add(_profile())
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    engagement = usecase.quick_start(actor(), {"base_url": "example.com", "authorization_attested": True})
    first = repo.repo.list(AuthorizationAttestation, engagement_id=engagement.id)[0]
    second = usecase.attest(actor(), engagement.id, source_ip="10.0.0.1", user_agent="browser")
    current = repo.repo.list(AuthorizationAttestation, engagement_id=engagement.id)
    assert len(current) == 2
    assert next(item for item in current if item.id == first.id).revoked_at is not None
    assert second.id != first.id
    assert usecase.authorization(actor(), engagement.id)["valid"] is True
