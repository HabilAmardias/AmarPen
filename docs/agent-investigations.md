# Bounded agent investigations

Discovery, specialist testing, and validation tasks can now continue after their first observation. The model returns a schema-validated decision, and the backend schedules at most one approved MCP action for the next turn. The next model call receives the recorded observations, evidence references, permitted capabilities, remaining budgets, and current objective.

## Decisions

- `TOOL_ACTION`: provide `tool`, `arguments`, and a concise `reason`. Supported synchronous investigation capabilities are `http_request`, `http_probe`, and discovery-only `map_endpoints`, further restricted by the run's pinned manifest. Arbitrary commands and unreviewed capabilities are rejected.
- `NEEDS_PREREQUISITE`: provide `prerequisite` and `reason`. The objective ends inconclusively with an explicit blocker; an unavailable identity or workflow state is never represented as a successful test.
- `FINISH`: provide `reason` and the existing role-specific final fields. Technical failures cannot produce passing coverage. Older pinned prompts may still return their original final contract, but unknown fields and disconnected `tool_actions` arrays are rejected.

Example continuation:

```json
{
  "decision": "TOOL_ACTION",
  "tool": "http_request",
  "arguments": {
    "target": "https://authorized.example/search?q=benign-marker",
    "method": "GET"
  },
  "reason": "Compare the observed parameter with the authorized baseline"
}
```

## Execution guarantees and limits

Task checkpoints store pending actions, in-flight intent, observation IDs, turn counts, and stop reasons. Observation bodies and evidence references are durable task-result records. JSON repair reuses observations without repeating completed HTTP requests. A restarted task with an uncertain in-flight result requires reconciliation rather than automatic replay.

Each turn consumes a model call. Each proposed follow-up action consumes the global investigation iteration budget. Merely scheduling validation, risk assessment, reporting, or fallback endpoint tasks no longer consumes that iteration budget. The existing task `model_budget` and `iteration_budget` bound investigation turns, both defaulting to eight for newly created tasks. Global request, model, task, and iteration limits still apply. Failed handoff allocations create audited budget limitations and partial assessment metadata.

Request task keys distinguish method, identity, body, content type, case-sensitive URL/query data, and feedback purpose. Both normal and fallback planning use this key. Request bodies and content types are forwarded to MCP. Non-read methods require an explicitly approved scenario: state-change effects or an Administrator-configured `applicability.allowed_methods` entry for an approved read-only operation such as POST-based search. Existing prohibited-effect rules remain enforced. Authentication secrets remain resolved by trusted identity services.

Repeating a successful identical action stops the investigation as inconclusive instead of spending the remaining budget. Safe, repeatable operations with transient failures can be retried at most twice, with delayed scheduling for 429/5xx responses. State-changing operations with uncertain outcomes require reconciliation. Crawler retries each reserve request budget and check run control. HTTP query strings are retained during discovery.

Pause/stop and changed task leases are rechecked around external responses. Stale results cannot schedule follow-ups or overwrite a replacement lease. Stop confirmation waits for active tasks; expired unconfirmed execution produces an actionable failure instead of reporting STOPPED. This is not proof that a previously transmitted request or target-side effect was undone.

A run with discovery alone fails to claim completed testing. Run snapshots expose `assessment_completeness` and `assessment_limitations`; inconclusive coverage, failed objectives, pending validation, incomplete discovery, or budget limitations produce a partial assessment. Agent preview reports carry the same partial status and limitations. Existing Reviewer approval remains required.

## Upgrade an existing installation

1. Deploy the backend and worker together. This change uses existing columns and task-result records; it adds no database tables.
2. Startup preserves active prompt releases and creates suggested upgrade drafts. An Administrator must review and publish the drafts for the investigation roles and the feedback-aware orchestrator, validate a complete release using the intended model profiles, and activate it through the existing prompt-management flow. Startup never publishes or replaces an Administrator's release automatically.
3. Start a new run to pin that release. Existing and resumed runs retain their original pinned instructions; their behavior is not silently changed by editing a prompt.
4. Verify the model profile can produce the investigation decision contract. The local/cloud OpenAI-compatible gateway retains strict provider schemas for compatible contracts; unions and conditional contracts use JSON mode plus the full backend schema validator. Native model tool calling is not required. MCP execution remains on-premises. See the [official OpenAI schema restrictions and JSON mode guidance](https://developers.openai.com/api/docs/guides/structured-outputs).

The rollout requires prompt activation to benefit from the new exploratory decisions. Keeping a legacy terminal-only prompt retains its conservative terminal behavior.

## Verification and remaining scope

Regression tests cover multiple informative actions, checkpoint restart, method/identity separation, body forwarding, rejected actions, bounded retries, prerequisite blockers, JSON repair without network replay, validation re-entry, budget accounting, incomplete assessments, prompt-release preservation, fresh database reads, and pause/stop or replacement-lease races. Tests use controlled fakes and local database fixtures; no live target or real inference endpoint is exercised.

This change does not add browser automation, autonomous email verification, a general login/session-refresh capability, unrestricted scanner access, or an exhaustive coverage optimizer. Those capabilities require their own reviewed adapters and acceptance fixtures. Model selection and actual finding effectiveness should be evaluated against controlled lab applications after the prompt upgrade.
