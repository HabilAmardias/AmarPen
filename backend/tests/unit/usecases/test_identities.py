import httpx

from pentest_platform.domain.entities import Run, Task
from pentest_platform.usecases.identities import IdentityProvisioningUsecase
from tests.fakes import FakeSecretCipher


def test_provisioning_registers_form_identity_and_stores_cookie(base_kwargs, repo, engagement):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/register":
            return httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text='<form method="post" action="/register"><input type="hidden" name="csrf" value="abc"><input name="username"><input name="email"><input type="password" name="password"><input type="password" name="password_confirm"><button type="submit">Go</button></form>',
            )
        if request.method == "POST" and request.url.path == "/register":
            return httpx.Response(201, headers={"set-cookie": "session=test-session; Path=/"})
        return httpx.Response(404)

    run = Run(id="run-1", engagement_id=engagement.id)
    task = Task(id="task-1", run_id=run.id, scenario_id="", worker_id="worker")
    repo.repo.add(run)
    repo.repo.add(task)
    usecase = IdentityProvisioningUsecase(**base_kwargs, secret_cipher=FakeSecretCipher(), transport=httpx.MockTransport(handler))
    created = usecase.provision(
        repo,
        run,
        engagement,
        task,
        [{"url": "https://example.com/register", "path": "/register", "methods": ["POST"]}],
    )
    assert len(created) == 2
    assert created[0].origin == "self_registered"
    assert created[0].status == "ACTIVE"
    headers, cookies = usecase.identity_for_run(repo, run.id, created[0].id)
    assert headers == {}
    assert cookies["session"] == "test-session"


def test_provisioning_skips_without_registration(base_kwargs, repo, engagement):
    run = Run(id="run-1", engagement_id=engagement.id)
    task = Task(id="task-1", run_id=run.id, scenario_id="", worker_id="worker")
    repo.repo.add(run)
    repo.repo.add(task)
    usecase = IdentityProvisioningUsecase(**base_kwargs, secret_cipher=FakeSecretCipher(), transport=httpx.MockTransport(lambda _: httpx.Response(404)))
    assert usecase.provision(repo, run, engagement, task, [{"url": "https://example.com/docs", "path": "/docs", "methods": ["GET"]}]) == []


def test_provisioning_respects_existing_identities(base_kwargs, repo, engagement):
    from pentest_platform.domain.entities import TestIdentity

    run = Run(id="run-1", engagement_id=engagement.id)
    task = Task(id="task-1", run_id=run.id, scenario_id="", worker_id="worker")
    repo.repo.add(run)
    repo.repo.add(task)
    for index in range(2):
        repo.repo.add(TestIdentity(id=f"identity-{index}", engagement_id=engagement.id, label=f"u{index}"))
    usecase = IdentityProvisioningUsecase(**base_kwargs, secret_cipher=FakeSecretCipher())
    existing = usecase.provision(repo, run, engagement, task, [])
    assert len(existing) == 2


def test_provisioning_marks_verification_required(base_kwargs, repo, engagement):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, headers={"content-type": "text/html"}, text='<form method="post"><input name="email"><input name="password"></form>')
        return httpx.Response(201, text="Please verify your email before signing in")

    run = Run(id="run-1", engagement_id=engagement.id)
    task = Task(id="task-1", run_id=run.id, scenario_id="", worker_id="worker")
    repo.repo.add(run)
    repo.repo.add(task)
    usecase = IdentityProvisioningUsecase(**base_kwargs, secret_cipher=FakeSecretCipher(), transport=httpx.MockTransport(handler))
    created = usecase.provision(repo, run, engagement, task, [{"url": "https://example.com/register", "path": "/register", "methods": ["POST"]}])
    assert created[0].status == "VERIFICATION_REQUIRED"


def test_provisioning_falls_back_to_login_form(base_kwargs, repo, engagement):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/register" and request.method == "GET":
            return httpx.Response(200, headers={"content-type": "text/html"}, text='<form method="post" action="/register"><input name="username"><input name="password"></form>')
        if request.url.path == "/register":
            return httpx.Response(201)
        if request.url.path == "/login" and request.method == "GET":
            return httpx.Response(200, headers={"content-type": "text/html"}, text='<form method="post" action="/login"><input name="username"><input name="password"></form>')
        if request.url.path == "/login":
            return httpx.Response(200, headers={"set-cookie": "auth=logged-in; Path=/"})
        return httpx.Response(404)

    run = Run(id="run-1", engagement_id=engagement.id)
    task = Task(id="task-1", run_id=run.id, scenario_id="", worker_id="worker")
    repo.repo.add(run)
    repo.repo.add(task)
    usecase = IdentityProvisioningUsecase(**base_kwargs, secret_cipher=FakeSecretCipher(), transport=httpx.MockTransport(handler))
    created = usecase.provision(
        repo,
        run,
        engagement,
        task,
        [
            {"url": "https://example.com/register", "path": "/register", "methods": ["POST"]},
            {"url": "https://example.com/login", "path": "/login", "methods": ["POST"]},
        ],
    )
    assert created
    headers, cookies = usecase.identity_for_run(repo, run.id, created[0].id)
    assert cookies.get("auth") == "logged-in"


def test_identity_for_run_missing_session_returns_empty(base_kwargs, repo):
    usecase = IdentityProvisioningUsecase(**base_kwargs, secret_cipher=FakeSecretCipher())
    assert usecase.identity_for_run(repo, "none", "none") == ({}, {})


def test_candidate_filters():
    endpoints = [
        {"path": "/register", "methods": ["POST"]},
        {"path": "/login", "methods": ["POST"]},
        {"path": "/docs", "methods": ["GET"]},
    ]
    assert len(IdentityProvisioningUsecase._registration_candidates(endpoints)) == 1
    assert len(IdentityProvisioningUsecase._login_candidates(endpoints)) == 1
