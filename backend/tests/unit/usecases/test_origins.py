import pytest

from pentest_platform.domain.entities import AuthorizationAttestation, DiscoveredOrigin, ModelProfile
from pentest_platform.domain.errors import ConflictError, ValidationError
from pentest_platform.usecases.engagements import EngagementUsecase
from tests.fakes import actor


def _profile():
    return ModelProfile(
        id="model-1",
        name="ready",
        base_url="http://model/v1",
        model="mock",
        capabilities=["chat", "structured_outputs"],
        last_test_status="REACHABLE",
        last_test_detail={"structured_outputs": True},
    )


def _origin(engagement_id="id-1", host="api.example.com"):
    return DiscoveredOrigin(
        id="origin-1",
        engagement_id=engagement_id,
        run_id="run-1",
        scheme="https",
        host=host,
        source_type="js",
        source_url="https://example.com/app.js",
        sample_paths=["/api/v1/me"],
    )


def test_owner_can_approve_related_discovered_origin(base_kwargs, repo, evidence_store):
    repo.repo.add(_profile())
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    engagement = usecase.quick_start(actor(), {"base_url": "https://example.com", "authorization_attested": True})
    original_scope_version = engagement.scope_version
    origin = _origin(engagement.id)
    repo.repo.add(origin)
    result = usecase.approve_origin(
        actor(roles=("Analyst",)),
        engagement.id,
        origin.id,
        engagement.config_version,
        "Referenced by approved app",
    )
    assert result["origin"].status == "APPROVED"
    updated = repo.repo.get(type(engagement), engagement.id)
    assert "api.example.com" in updated.targets
    assert updated.scope_version == original_scope_version + 1
    attestation = repo.repo.list(AuthorizationAttestation, engagement_id=engagement.id)[-1]
    assert attestation.method == "owner_scope_extension"
    assert "api.example.com" in attestation.attestation_text
    assert usecase.authorization(actor(), engagement.id)["valid"] is True


def test_unrelated_origin_requires_administrator(base_kwargs, repo, evidence_store):
    repo.repo.add(_profile())
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    engagement = usecase.quick_start(actor(), {"base_url": "https://example.com", "authorization_attested": True})
    origin = _origin(engagement.id, host="other.example.net")
    repo.repo.add(origin)
    with pytest.raises(ValidationError):
        usecase.approve_origin(actor(roles=("Analyst",)), engagement.id, origin.id, engagement.config_version)


def test_rejected_origin_does_not_change_scope(base_kwargs, repo, evidence_store):
    repo.repo.add(_profile())
    usecase = EngagementUsecase(**base_kwargs, evidence_store=evidence_store)
    engagement = usecase.quick_start(actor(), {"base_url": "https://example.com", "authorization_attested": True})
    origin = _origin(engagement.id)
    repo.repo.add(origin)
    rejected = usecase.reject_origin(actor(), engagement.id, origin.id, engagement.config_version, "No")
    assert rejected.status == "REJECTED"
    updated = repo.repo.get(type(engagement), engagement.id)
    assert updated.targets == engagement.targets
    with pytest.raises(ConflictError):
        usecase.approve_origin(actor(), engagement.id, origin.id, engagement.config_version)
