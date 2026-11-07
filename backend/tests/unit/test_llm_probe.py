import json

import httpx

from pentest_platform.adapters.llm.openai_compatible import OpenAICompatibleGateway
from pentest_platform.domain.entities import ModelProfile
from tests.fakes import FakeSecretCipher


def profile(api_key_encrypted: str = "") -> ModelProfile:
    return ModelProfile(
        id="p1",
        name="test",
        base_url="http://model/v1",
        model="gemma",
        capabilities=["chat", "structured_outputs"],
        api_key_encrypted=api_key_encrypted,
        last_test_status="REACHABLE",
        last_test_detail={"structured_outputs": False},
    )


def test_probe_prompt_contains_exact_object_and_validates_schema():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "gemma"}]})
        body = json.loads(request.content)
        if "response_format" in body:
            captured["prompt"] = body["messages"][0]["content"]
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": '{"status":"ok","probe_id":"sentinel-42"}'}}]},
            )
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    gateway = OpenAICompatibleGateway(transport=httpx.MockTransport(handler))
    result = gateway.probe(profile())
    assert result["structured_outputs"] is True
    assert "sentinel-42" in captured["prompt"]


def test_probe_rejects_clarification_and_non_schema_output():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": []})
        body = json.loads(request.content)
        if "response_format" in body:
            return httpx.Response(200, json={"choices": [{"message": {"content": "What object do you want?"}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    result = OpenAICompatibleGateway(transport=httpx.MockTransport(handler)).probe(profile())
    assert result["structured_outputs"] is False
    assert result["reachable"] is True


def test_probe_rejects_wrong_enum_and_missing_probe_id():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": []})
        body = json.loads(request.content)
        if "response_format" in body:
            return httpx.Response(200, json={"choices": [{"message": {"content": '{"status":"bad"}'}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    result = OpenAICompatibleGateway(transport=httpx.MockTransport(handler)).probe(profile())
    assert result["structured_outputs"] is False


def test_probe_reports_provider_rejection():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": []})
        body = json.loads(request.content)
        if "response_format" in body:
            return httpx.Response(400, json={"error": "response_format unsupported"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    result = OpenAICompatibleGateway(transport=httpx.MockTransport(handler)).probe(profile())
    assert result["structured_outputs"] is False
    assert result["reachable"] is True


def test_bearer_key_is_sent_to_completion_probe_and_health():
    seen: list[str] = []
    schema = {
        "type": "object",
        "required": ["status"],
        "properties": {"status": {"enum": ["ok"]}},
        "additionalProperties": False,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("authorization", ""))
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "gemma"}]})
        body = json.loads(request.content)
        if "response_format" in body:
            return httpx.Response(200, json={"choices": [{"message": {"content": '{"status":"ok"}'}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    gateway = OpenAICompatibleGateway(
        transport=httpx.MockTransport(handler),
        secret_cipher=FakeSecretCipher(),
    )
    secured = profile("enc:cloud-secret")
    assert gateway.health(secured) is True
    gateway.complete(secured, [{"role": "user", "content": "hello"}], schema)
    gateway.probe(secured)
    assert seen
    assert all(value == "Bearer cloud-secret" for value in seen)


def test_unreadable_stored_key_does_not_reach_provider():
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={"data": []})

    gateway = OpenAICompatibleGateway(transport=httpx.MockTransport(handler), secret_cipher=None)
    result = gateway.probe(profile("enc:unreadable"))
    assert result["status"] == "UNREACHABLE"
    assert result["structured_outputs"] is False
    assert called is False


def test_structured_output_accepts_markdown_fenced_json():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "gemma"}]})
        body = json.loads(request.content)
        if "response_format" in body:
            content = '```json\n{"status":"ok","probe_id":"sentinel-42"}\n```'
            return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    gateway = OpenAICompatibleGateway(transport=httpx.MockTransport(handler))
    assert gateway.probe(profile())["structured_outputs"] is True


def test_structured_output_extracts_json_from_explanatory_text():
    schema = {
        "type": "object",
        "required": ["status"],
        "properties": {"status": {"enum": ["ok"]}},
        "additionalProperties": False,
    }

    def handler(_request: httpx.Request) -> httpx.Response:
        content = 'Here is the requested object:\n{"status":"ok"}\nUse it as planned.'
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    gateway = OpenAICompatibleGateway(transport=httpx.MockTransport(handler))
    result = gateway.complete(profile(), [{"role": "user", "content": "go"}], schema)
    assert result["content"] == {"status": "ok"}


def test_investigation_union_uses_json_mode_and_still_validates_locally():
    import pytest

    from pentest_platform.domain.agents import AGENT_CONTRACTS
    from pentest_platform.domain.errors import ValidationError
    responses = [
        {"decision": "TOOL_ACTION", "tool": "http_request", "arguments": {"target": "https://example.com"}, "reason": "Inspect the baseline"},
        {"decision": "TOOL_ACTION", "tool": "unrestricted_shell", "arguments": {}, "reason": "Forbidden"},
    ]
    def handler(request):
        body = json.loads(request.content)
        assert body["response_format"] == {"type": "json_object"}
        assert "output contract" in body["messages"][-1]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(responses.pop(0))}}]})
    gateway = OpenAICompatibleGateway(transport=httpx.MockTransport(handler))
    schema = AGENT_CONTRACTS["web_testing"].schema
    assert gateway.complete(profile(), [{"role": "user", "content": "Investigate"}], schema)["content"]["tool"] == "http_request"
    with pytest.raises(ValidationError):
        gateway.complete(profile(), [{"role": "user", "content": "Investigate"}], schema)
