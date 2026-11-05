import hashlib

import pytest

from pentest_platform.domain.entities import User
from pentest_platform.domain.errors import (
    ConflictError,
    ForbiddenError,
    RateLimitedError,
    UnauthenticatedError,
)
from pentest_platform.usecases.auth import AuthUsecase
from tests.fakes import actor, user


def make_auth(base_kwargs, passwords, totp):
    return AuthUsecase(**base_kwargs, passwords=passwords, totp=totp, bootstrap_token="boot")


def test_bootstrap_is_one_time(base_kwargs, passwords, totp):
    usecase = make_auth(base_kwargs, passwords, totp)
    created = usecase.bootstrap("boot", "admin", "correct horse battery")
    assert created.roles == ["Administrator", "Analyst", "Reviewer"]
    with pytest.raises(ConflictError):
        usecase.bootstrap("boot", "second", "correct horse battery")


def test_bootstrap_rejects_bad_token(base_kwargs, passwords, totp):
    usecase = make_auth(base_kwargs, passwords, totp)
    with pytest.raises(ForbiddenError):
        usecase.bootstrap("wrong", "admin", "correct horse battery")


def test_password_alone_does_not_create_full_session(base_kwargs, repo, passwords, totp):
    repo.repo.add(user())
    usecase = make_auth(base_kwargs, passwords, totp)
    result = usecase.login("admin", "correct horse battery")
    assert result.session.preauth is True
    assert result.requires_totp is True
    with pytest.raises(UnauthenticatedError):
        usecase.current_session(result.token)


def test_invalid_password_is_audited_and_rejected(base_kwargs, repo, passwords, totp, audit):
    repo.repo.add(user())
    usecase = make_auth(base_kwargs, passwords, totp)
    with pytest.raises(UnauthenticatedError):
        usecase.login("admin", "wrong password")
    assert any(event.action == "auth.failed" for event in audit.events)


def test_throttling_blocks_repeated_failures(base_kwargs, repo, passwords, totp, clock):
    repo.repo.add(user())
    usecase = make_auth(base_kwargs, passwords, totp)
    for _ in range(5):
        with pytest.raises(UnauthenticatedError):
            usecase.login("admin", "wrong password")
    with pytest.raises(RateLimitedError):
        usecase.login("admin", "wrong password")


def test_totp_completes_session_and_prevents_replay(base_kwargs, repo, passwords, totp):
    repo.repo.add(user())
    usecase = make_auth(base_kwargs, passwords, totp)
    preauth = usecase.login("admin", "correct horse battery")
    full = usecase.verify_totp(preauth.token, "123456")
    assert full.session.preauth is False
    assert usecase.current_session(full.token).user.username == "admin"
    preauth2 = usecase.login("admin", "correct horse battery")
    with pytest.raises(UnauthenticatedError):
        usecase.verify_totp(preauth2.token, "123456")


def test_enrollment_verifies_before_activation(base_kwargs, repo, passwords, totp):
    pending = user(totp_enabled=False)
    pending.totp_secret_enc = ""
    repo.repo.add(pending)
    usecase = make_auth(base_kwargs, passwords, totp)
    preauth = usecase.login("admin", "correct horse battery")
    started = usecase.enrollment_start(preauth.token)
    assert started["secret"]
    with pytest.raises(UnauthenticatedError):
        usecase.enrollment_verify(preauth.token, "000000")
    verified = usecase.enrollment_verify(preauth.token, "123456")
    assert verified.recovery_codes and len(verified.recovery_codes) == 10
    stored = repo.repo.get(User, "user-1")
    assert stored.totp_enabled is True
    assert stored.recovery_codes


def test_logout_revokes_session(base_kwargs, repo, passwords, totp):
    repo.repo.add(user())
    usecase = make_auth(base_kwargs, passwords, totp)
    result = usecase.login("admin", "correct horse battery")
    full = usecase.verify_totp(result.token, "123456")
    usecase.logout(full.token)
    with pytest.raises(UnauthenticatedError):
        usecase.current_session(full.token)


def test_recovery_code_is_single_use(base_kwargs, repo, passwords, totp):
    stored = user()
    stored.recovery_codes = [hashlib.sha256(b"recovery-code").hexdigest()]
    repo.repo.add(stored)
    usecase = make_auth(base_kwargs, passwords, totp)
    usecase.recovery("admin", "recovery-code", "new correct horse battery")
    with pytest.raises(UnauthenticatedError):
        usecase.recovery("admin", "recovery-code", "another correct horse")


def test_change_password_revokes_other_sessions(base_kwargs, repo, passwords, totp):
    repo.repo.add(user())
    usecase = make_auth(base_kwargs, passwords, totp)
    first = usecase.login("admin", "correct horse battery")
    full = usecase.verify_totp(first.token, "123456")
    usecase.change_password(
        actor(),
        "correct horse battery",
        "new correct horse battery",
        full.token,
    )
    assert repo.repo.get(User, "user-1").password_hash == "hashed:new correct horse battery"
