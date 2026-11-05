import pytest

from pentest_platform.domain.agents import REQUIRED_AGENT_ROLES
from pentest_platform.domain.errors import ConflictError, ForbiddenError, ValidationError
from pentest_platform.usecases.prompts import PromptUsecase
from tests.fakes import actor


def make_usecase(base_kwargs):
    return PromptUsecase(**base_kwargs)


def test_non_administrator_cannot_read_bodies(base_kwargs):
    usecase = make_usecase(base_kwargs)
    prompts = usecase.list_prompts(actor(roles=("Analyst",)))
    assert prompts == []
    with pytest.raises(ForbiddenError):
        usecase.list_prompts(actor(roles=("Analyst",)), include_bodies=True)


def test_published_versions_are_immutable(base_kwargs):
    usecase = make_usecase(base_kwargs)
    draft = usecase.create_draft(actor(), "agent-test", "orchestrator", "purpose", "Act safely.", "initial")
    published = usecase.publish(actor(), draft.id)
    assert published.state == "PUBLISHED"
    with pytest.raises(ConflictError):
        usecase.update_draft(actor(), published.id, "changed", "reason", published.version)


def test_validation_blocks_unsafe_placeholder_content(base_kwargs):
    usecase = make_usecase(base_kwargs)
    with pytest.raises(ValidationError):
        usecase.create_draft(actor(), "agent-test", "orchestrator", "purpose", "Run {{secret}}", "reason")


def complete_manifest(usecase: PromptUsecase) -> dict:
    manifest = {}
    for role in sorted(REQUIRED_AGENT_ROLES):
        prompt = usecase.create_draft(actor(), f"agent-{role}", role, "purpose", f"Act safely as {role}.", "initial")
        usecase.publish(actor(), prompt.id)
        manifest[role] = prompt.id
    return manifest


def test_release_activation_and_pinned_resolution(base_kwargs):
    usecase = make_usecase(base_kwargs)
    manifest = complete_manifest(usecase)
    release = usecase.create_release(actor(), "release-1", manifest)
    with pytest.raises(ConflictError):
        usecase.activate_release(actor(), release.id)
    validated = usecase.validate_release(actor(), release.id)
    activated = usecase.activate_release(actor(), validated.id)
    assert activated.state == "ACTIVE"
    pinned = usecase.resolve_pinned(activated.id)
    assert pinned["prompts"]["orchestrator"]["body"] == "Act safely as orchestrator."
