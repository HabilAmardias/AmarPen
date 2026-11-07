import pytest

from pentest_platform.controllers.internal_mcp import require_mcp_service_token
from pentest_platform.domain.errors import ForbiddenError


class Container:
    class Settings:
        mcp_service_token = "service-token"

    settings = Settings()


def test_mcp_service_token_is_required():
    with pytest.raises(ForbiddenError):
        require_mcp_service_token(Container(), None)
    with pytest.raises(ForbiddenError):
        require_mcp_service_token(Container(), "wrong")
    require_mcp_service_token(Container(), "service-token")
