import pytest

from pentest_platform.domain.errors import ForbiddenError
from pentest_platform.usecases.admin import AdminUsecase
from tests.fakes import actor


def test_admin_guards_model_profiles(base_kwargs):
    usecase = AdminUsecase(**base_kwargs)
    with pytest.raises(ForbiddenError):
        usecase.list_model_profiles(actor(roles=("Analyst",)))
    profile = usecase.create_model_profile(
        actor(),
        {"name": "local", "base_url": "http://localhost:8080/v1", "model": "mock"},
    )
    assert profile.name == "local"
    assert usecase.list_model_profiles(actor())[0].id == profile.id


def test_risk_policy_activation_is_exclusive(base_kwargs):
    usecase = AdminUsecase(**base_kwargs)
    first = usecase.create_risk_policy(actor(), "first")
    second = usecase.create_risk_policy(actor(), "second")
    usecase.activate_risk_policy(actor(), first.id)
    usecase.activate_risk_policy(actor(), second.id)
    policies = usecase.list_risk_policies(actor())
    active = [policy for policy in policies if policy.active]
    assert len(active) == 1
    assert active[0].id == second.id


def test_settings_increment_version(base_kwargs):
    usecase = AdminUsecase(**base_kwargs)
    first = usecase.update_setting(actor(), "session.timeout", {"minutes": 30})
    first_version = first.version
    second = usecase.update_setting(actor(), "session.timeout", {"minutes": 15})
    assert second.version == first_version + 1
