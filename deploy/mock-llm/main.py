import json
import re
import time
from typing import Any

from fastapi import FastAPI, Request

app = FastAPI(title="Mock OpenAI-compatible model", version="0.1.0")


@app.get("/v1/models")
def models() -> dict:
    return {"object": "list", "data": [{"id": "mock-pentest", "object": "model", "created": int(time.time())}]}


@app.post("/v1/chat/completions")
async def chat(request: Request) -> dict[str, Any]:
    body = await request.json()
    messages = body.get("messages", [])
    context = _context(messages)
    role = context.get("agent_role", "orchestrator")
    payload = _payload_for_role(role, context)
    content = json.dumps(payload)
    return {
        "id": f"chatcmpl-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.get("model", "mock-pentest"),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": sum(len(message.get("content", "")) for message in messages) // 4, "completion_tokens": 50},
    }


def _context(messages: list[dict]) -> dict:
    for message in messages:
        content = message.get("content", "")
        marker = "AGENT_CONTEXT:"
        if marker in content:
            try:
                return json.loads(content.split(marker, 1)[1].strip())
            except json.JSONDecodeError:
                return {}
    return {}


def _payload_for_role(role: str, context: dict) -> dict:
    targets = context.get("targets", [])
    target = targets[0] if targets else "example.com"
    catalogue = context.get("catalogue", [])
    if role == "orchestrator":
        discovery_scenarios = [item for item in catalogue if item.get("agent_role") == "discovery"]
        discovery_key = discovery_scenarios[0]["key"] if discovery_scenarios else ""
        dependency = f"discovery:{discovery_key}:{target}".lower()
        tasks = [
            {
                "role": "discovery",
                "kind": "discovery",
                "scenario_key": discovery_key,
                "asset": target,
                "reason": "Map the approved target before specialist testing",
                "depends_on": [],
            }
        ]
        for specialist_role in ("web_testing", "api_testing", "authorization_business_logic"):
            candidates = [item for item in catalogue if item.get("agent_role") == specialist_role]
            if candidates:
                tasks.append(
                    {
                        "role": specialist_role,
                        "kind": "test",
                        "scenario_key": candidates[0]["key"],
                        "asset": target,
                        "reason": f"Run bounded {specialist_role} scenario",
                        "depends_on": [dependency] if discovery_key else [],
                    }
                )
        return {"tasks": tasks, "limitations": []}
    if role == "discovery":
        return {"assets": [{"kind": "target", "value": target}], "limitations": []}
    if role in {"web_testing", "api_testing", "authorization_business_logic"}:
        return {"candidates": [], "coverage_status": "TESTED_NO_ISSUE_OBSERVED", "limitations": []}
    if role == "validation":
        return {"verdict": "INCONCLUSIVE", "rationale": "Mock validation requires analyst review", "limitations": ["mock profile"]}
    if role == "risk_assessment":
        return {
            "cvss_vector": "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:N",
            "cvss_rationale": {"AV": "network"},
            "business_likelihood": 4,
            "business_impact": 4,
            "business_rationale": "Mock business context",
            "confidence": "high",
            "limitations": ["mock profile"],
        }
    if role == "reporting":
        return {
            "executive_summary": "Mock agent draft. Review coverage and findings before approval.",
            "scope": "Authorized external targets recorded on the engagement.",
            "methodology": "Approved scenario catalogue executed by backend-controlled agent tasks.",
            "limitations": ["Mock model profile; validation is analyst-reviewed."],
        }
    return {}
