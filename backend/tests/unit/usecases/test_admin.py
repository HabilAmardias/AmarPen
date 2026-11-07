import pytest

from pentest_platform.domain.errors import ForbiddenError
from pentest_platform.usecases.admin import AdminUsecase
from tests.fakes import FakeLlmGateway, FakeSecretCipher, actor


def test_admin_guards_model_profiles(base_kwargs):
    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(), secret_cipher=FakeSecretCipher())
    with pytest.raises(ForbiddenError):
        usecase.list_model_profiles(actor(roles=("Analyst",)))
    profile = usecase.create_model_profile(
        actor(),
        {"name": "local", "base_url": "http://localhost:8080/v1", "model": "mock"},
    )
    assert profile.name == "local"
    assert usecase.list_model_profiles(actor())[0].id == profile.id


def test_risk_policy_activation_is_exclusive(base_kwargs):
    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(), secret_cipher=FakeSecretCipher())
    first = usecase.create_risk_policy(actor(), "first")
    second = usecase.create_risk_policy(actor(), "second")
    usecase.activate_risk_policy(actor(), first.id)
    usecase.activate_risk_policy(actor(), second.id)
    policies = usecase.list_risk_policies(actor())
    active = [policy for policy in policies if policy.active]
    assert len(active) == 1
    assert active[0].id == second.id


def test_model_profile_probe_is_persisted(base_kwargs, repo):
    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(), secret_cipher=FakeSecretCipher())
    profile = usecase.create_model_profile(
        actor(),
        {"name": "local", "base_url": "http://localhost:8080/v1", "model": "mock"},
    )
    assert profile.last_test_status == "REACHABLE"
    assert profile.last_test_detail["chat_ok"] is True
    tested = usecase.test_model_profile(actor(), profile.id)
    assert tested.last_tested_at is not None


def test_model_profile_probe_failure_is_visible(base_kwargs):
    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(fail=True), secret_cipher=FakeSecretCipher())
    profile = usecase.create_model_profile(
        actor(),
        {"name": "down", "base_url": "http://localhost:8080/v1", "model": "mock"},
    )
    assert profile.last_test_status == "UNREACHABLE"
    assert profile.last_test_detail["reachable"] is False


def test_settings_increment_version(base_kwargs):
    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(), secret_cipher=FakeSecretCipher())
    first = usecase.update_setting(actor(), "session.timeout", {"minutes": 30})
    first_version = first.version
    second = usecase.update_setting(actor(), "session.timeout", {"minutes": 15})
    assert second.version == first_version + 1


def test_cloud_model_profile_requires_credential(base_kwargs):
    from pentest_platform.domain.errors import ValidationError

    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(), secret_cipher=FakeSecretCipher())
    with pytest.raises(ValidationError):
        usecase.create_model_profile(
            actor(),
            {
                "name": "cloud",
                "base_url": "https://api.example.com/v1",
                "model": "cloud-model",
                "data_boundary": "approved_cloud",
            },
        )


def test_model_profile_api_key_is_encrypted_and_not_audited(base_kwargs, repo, audit):
    from pentest_platform.domain.entities import ModelProfile

    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(), secret_cipher=FakeSecretCipher())
    profile = usecase.create_model_profile(
        actor(),
        {
            "name": "cloud",
            "base_url": "https://api.example.com/v1",
            "model": "cloud-model",
            "data_boundary": "approved_cloud",
            "api_key": "super-secret-key",
        },
    )
    stored = repo.repo.get(ModelProfile, profile.id)
    assert stored.api_key_encrypted == "enc:super-secret-key"
    assert stored.has_api_key is True
    assert all("super-secret-key" not in str(event.details) for event in audit.events)
    assert "api_key" not in audit.events[-1].details


def test_model_profile_api_key_can_be_rotated_and_cleared(base_kwargs, repo):
    from pentest_platform.domain.entities import ModelProfile

    usecase = AdminUsecase(**base_kwargs, llm_gateway=FakeLlmGateway(), secret_cipher=FakeSecretCipher())
    profile = usecase.create_model_profile(
        actor(),
        {"name": "local", "base_url": "http://localhost:8080/v1", "model": "mock", "api_key": "first-key"},
    )
    usecase.update_model_profile(actor(), profile.id, {"api_key": "second-key"})
    assert repo.repo.get(ModelProfile, profile.id).api_key_encrypted == "enc:second-key"
    usecase.update_model_profile(actor(), profile.id, {"clear_api_key": True})
    assert repo.repo.get(ModelProfile, profile.id).api_key_encrypted == ""
