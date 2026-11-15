import pytest

from pentest_platform.domain.entities import SkillPack
from pentest_platform.domain.errors import ConflictError, ValidationError
from pentest_platform.domain.skills import select_skill_cards
from pentest_platform.usecases.skills import SkillUsecase
from tests.fakes import actor


def skill(key="wstg.info", scenario="WSTG-INFO-01"):
    return {
        "key": key,
        "title": "Information gathering",
        "category": "wstg",
        "source_refs": [scenario],
        "hypothesis": "Map the target",
        "applicability": {"endpoint_types": ["web"], "methods": ["GET"]},
        "scenario_keys": [scenario],
        "prerequisites": [],
        "probe_strategy": ["baseline"],
        "evidence_criteria": ["observation"],
        "stop_conditions": ["scope mismatch"],
        "prompt_fragment": "Map before testing.",
    }


def make_usecase(base_kwargs):
    return SkillUsecase(**base_kwargs)


def test_skill_pack_and_release_lifecycle(base_kwargs, repo):
    usecase = make_usecase(base_kwargs)
    pack = usecase.create_pack(
        actor(),
        {"key": "wstg-web", "name": "WSTG", "category": "wstg", "skills": [skill()]},
    )
    assert pack.state == "DRAFT"
    assert usecase.validate_pack(actor(), pack.id)["passed"] is True
    published = usecase.publish_pack(actor(), pack.id)
    assert published.state == "PUBLISHED"
    release = usecase.create_release(actor(), "baseline", {"wstg-web": pack.id})
    validated = usecase.validate_release(actor(), release.id)
    assert validated.validated is True
    active = usecase.activate_release(actor(), release.id, "test")
    assert active.state == "ACTIVE"
    pinned = usecase.pin_for_run()
    assert pinned["manifest"]["wstg-web"] == pack.id
    assert pinned["packs"][0]["hash"] == published.integrity_hash
    rolled = usecase.rollback_release(actor(), release.id, "test")
    assert rolled.state == "ROLLED_BACK"


def test_invalid_skill_pack_is_rejected(base_kwargs):
    usecase = make_usecase(base_kwargs)
    with pytest.raises(ValidationError):
        usecase.create_pack(actor(), {"key": "bad", "name": "Bad", "skills": [{"key": ""}]})


def test_published_pack_is_immutable(base_kwargs):
    usecase = make_usecase(base_kwargs)
    pack = usecase.create_pack(actor(), {"key": "wstg-web", "name": "WSTG", "skills": [skill()]})
    usecase.publish_pack(actor(), pack.id)
    with pytest.raises(ConflictError):
        usecase.update_pack(actor(), pack.id, {"expected_version": pack.version, "name": "Changed"})


def test_release_requires_published_pack(base_kwargs):
    usecase = make_usecase(base_kwargs)
    pack = usecase.create_pack(actor(), {"key": "wstg-web", "name": "WSTG", "skills": [skill()]})
    with pytest.raises(ValidationError):
        usecase.create_release(actor(), "draft", {"wstg-web": pack.id})


def test_skill_selector_filters_by_applicability(base_kwargs, repo):
    pack = SkillPack(id="pack-1", key="wstg-web", name="WSTG", version=1, category="wstg", skills=[skill()])
    assets = [{"kind": "endpoint", "value": "https://example.com/", "metadata": {"content_type": "text/html", "methods": ["GET"]}}]
    cards = select_skill_cards([pack], role="web_testing", assets=assets, identity_count=0)
    assert cards[0]["key"] == "wstg.info"
    assert select_skill_cards([pack], role="web_testing", assets=assets, identity_count=0, task=type("T", (), {"asset": assets[0]["value"], "method": "POST"})()) == []
