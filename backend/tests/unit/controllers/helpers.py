from fastapi.testclient import TestClient

from pentest_platform.bootstrap.app import create_app
from pentest_platform.bootstrap.config import Settings
from tests.fakes import FakeContainer


def make_client(overrides: dict, settings: Settings | None = None) -> TestClient:
    settings = settings or Settings(database_url="sqlite:///:memory:", seed_baseline=False)
    container = FakeContainer(settings)
    app = create_app(settings, container=container)
    app.dependency_overrides.update(overrides)
    app.state.container = container
    return TestClient(app)
