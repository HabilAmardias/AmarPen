import pytest

from pentest_platform.domain.entities import Run, Session, User
from pentest_platform.domain.errors import ConflictError, ForbiddenError, ValidationError
from pentest_platform.usecases.access import AccessUsecase
from tests.fakes import actor


def make_access(base_kwargs, passwords):
    return AccessUsecase(**base_kwargs, passwords=passwords)


def test_access_requires_administrator(base_kwargs, passwords):
    usecase = make_access(base_kwargs, passwords)
    with pytest.raises(ForbiddenError):
        usecase.list_users(actor(roles=("Analyst",)))


def test_create_user_returns_temporary_password(base_kwargs, passwords, repo):
    usecase = make_access(base_kwargs, passwords)
    created, temporary = usecase.create_user(actor(), "analyst1", ["Analyst"])
    assert created.username == "analyst1"
    assert temporary
    with pytest.raises(ConflictError):
        usecase.create_user(actor(), "analyst1", ["Analyst"])
    assert repo.repo.count(type(created)) == 1


def test_disable_user_revokes_sessions_and_pauses_runs(base_kwargs, passwords, repo, ids):
    usecase = make_access(base_kwargs, passwords)
    target, _ = usecase.create_user(actor(), "analyst1", ["Analyst"])
    repo.repo.add(Session(id=ids.new_id(), user_id=target.id, token_hash="h", csrf_token="c"))
    run = Run(id=ids.new_id(), engagement_id="eng-1", state="RUNNING", initiated_by=target.id)
    repo.repo.add(run)
    disabled = usecase.set_disabled(actor(), target.id, True, "left company")
    assert disabled.disabled is True
    assert all(session.revoked for session in repo.repo.list(Session, user_id=target.id))
    assert repo.repo.get(Run, run.id).state == "PAUSING"


def test_admin_resets_mfa_and_password(base_kwargs, passwords, repo, ids):
    usecase = make_access(base_kwargs, passwords)
    target, _ = usecase.create_user(actor(), "analyst1", ["Analyst"])
    repo.repo.add(Session(id=ids.new_id(), user_id=target.id, token_hash="h", csrf_token="c"))
    reset = usecase.reset_mfa(actor(), target.id, "lost factor")
    assert reset.totp_enabled is False
    temporary = usecase.reset_password(actor(), target.id, "forgotten")
    assert temporary
    assert repo.repo.get(User, target.id).password_hash.startswith("hashed:")


def test_invalid_roles_are_rejected(base_kwargs, passwords):
    usecase = make_access(base_kwargs, passwords)
    with pytest.raises(ValidationError):
        usecase.create_user(actor(), "analyst1", ["Superuser"])
