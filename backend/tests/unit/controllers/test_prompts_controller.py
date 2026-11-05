from pentest_platform.controllers.deps import get_actor, get_prompts
from pentest_platform.domain.entities import PromptRelease, SystemPrompt
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

PROMPT = SystemPrompt(
    id="prompt-1",
    key="agent-orchestrator",
    agent_role="orchestrator",
    state="PUBLISHED",
    version=1,
    body="Act safely.",
    content_hash="hash",
)
RELEASE = PromptRelease(id="release-1", name="baseline", manifest={"orchestrator": "prompt-1"}, state="ACTIVE", validated=True)


class StubPrompts:
    def list_prompts(self, actor, include_bodies=False):
        item = {
            "id": PROMPT.id,
            "key": PROMPT.key,
            "agent_role": PROMPT.agent_role,
            "purpose": PROMPT.purpose,
            "state": PROMPT.state,
            "version": PROMPT.version,
            "content_hash": PROMPT.content_hash,
        }
        if include_bodies:
            item["body"] = PROMPT.body
        return [item]

    def create_draft(self, actor, key, agent_role, purpose, body, change_reason):
        return PROMPT

    def publish(self, actor, prompt_id):
        return PROMPT

    def list_releases(self, actor):
        return [RELEASE]


def test_prompt_metadata_hides_body_by_default():
    client = make_client({get_actor: lambda: actor(), get_prompts: lambda: StubPrompts()})
    response = client.get("/api/v1/prompts")
    assert response.status_code == 200
    assert "body" not in response.json()["items"][0]
    with_body = client.get("/api/v1/prompts?include_bodies=true")
    assert with_body.json()["items"][0]["body"] == "Act safely."


def test_prompt_publish_and_release_listing():
    client = make_client({get_actor: lambda: actor(), get_prompts: lambda: StubPrompts()})
    assert client.post("/api/v1/prompts/prompt-1/publish").status_code == 200
    assert client.get("/api/v1/prompts/releases/all").json()["items"][0]["state"] == "ACTIVE"
