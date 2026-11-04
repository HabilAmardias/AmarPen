# AI Penetration Testing Platform Non Functional Requirements Document

Version 1.1 | 4 November 2026 | MVP requirements baseline for review

Audience: Engineering, security, QA, deployment administrators, and acceptance reviewers.

Revision 1.1 adds quality gates for finding-based retests and Administrator-only system prompt management for each agent and configured LLM profile, including immutable provenance and execution pinning. User prompts and runtime task inputs are excluded from this management feature.

## 1 Purpose and authority

This document defines the quality attributes of the on-premises web and API penetration testing MVP. It complements the PRD outcomes and the FRD behavior. Security, correctness, scope enforcement, attribution, and honest execution state are mandatory properties. Numerical limits and sizing values in this document are proposed engineering baselines for DEC-01 through DEC-07 review; they are not measured capabilities or customer service commitments.

Acceptance evidence must identify hardware, software versions, configuration, model profile, test fixtures, workload, results, and reviewer. A numerical target becomes a release gate when the product owner and responsible engineering or security reviewer approve the baseline. Changes must remain traceable across all three requirement documents.

## 2 Proposed verification environment

Use a reproducible on-premises reference installation before capacity testing. A proposed starting profile is 8 vCPU, 16 GB RAM, and 100 GB available SSD storage for application services and workers. Local-model compute, model files, long-term evidence growth, backup capacity, and externally hosted identity services are not included in that sizing. The platform does not require an external identity service.

| Dimension | Proposed benchmark profile |
| --- | --- |
| Interactive workload | 10 simultaneously signed-in users with representative read and edit actions. |
| Execution workload | 2 active engagements and at most 4 active testing tasks in total. |
| Dataset | 1,000 discovered endpoints, 100 findings, and 1,000 evidence artifacts in the benchmark dataset. |
| PDF fixture | Up to 50 pages with 50 detailed findings and up to 50 MB of source artifacts, including required appendices. |
| External dependencies | Controlled target fixtures and simulated model latency and outages; evaluate real model profiles separately. |
| Measurement | Warm steady-state p95 latency over at least 1,000 representative API operations, with error rate and resource utilization recorded. |

These are test conditions, not hard product limits. Hardware and concurrency must be calibrated before deployment. Test traffic budgets are separate from platform capacity and must remain target-specific.

## 3 Security requirements

**NFR-SEC-001 Authentication material**

Passwords shall be salted and hashed using Argon2id through a maintained implementation. Proposed minimum parameters are 19 MiB memory, 2 iterations, and parallelism 1, with stronger settings selected after host calibration. TOTP secrets shall be encrypted with separately managed key material. Recovery codes shall be stored as hashes and consumed atomically.

Verification: Inspect stored records and configuration, verify code reuse rejection, and test key separation. No plaintext password, recovery code, or TOTP secret appears in application or audit logs. Applies to FR-AUTH-001 through FR-AUTH-006.

**NFR-SEC-002 Authentication policy**

Proposed defaults are a minimum password length of 12 characters, support for at least 128 characters and spaces, and no silent truncation. Use 6-digit, 30-second TOTP with an initial clock tolerance of one adjacent step, replay prevention, and synchronized server time. Suggested throttling begins after 5 failed attempts within 5 minutes, with bounded progressive delays and separate account and source controls.

Verification: Boundary, replay, concurrent verification, expiry, brute-force, and recovery tests pass. Confirm the chosen authenticator parameters are supported by the implementation. Final policy values require DEC-04 approval and must avoid indefinite attacker-triggered account lockout.

**NFR-SEC-003 Session and authorization protection**

Protected requests shall enforce backend identity and object-level access. Browser cookies shall use Secure, HttpOnly, and appropriate SameSite attributes, with CSRF protection for mutations. Proposed idle and absolute session timeouts are 30 minutes and 8 hours. Browser session expiry does not itself cancel an authorized background run.

Verification: Direct API and identifier-substitution tests fail across role and project boundaries. Logout and account disablement revoke sessions. Disabling an initiating account triggers the controlled pause required by FR-AUTH-006.

**NFR-SEC-004 Transport storage and secrets**

Use authenticated TLS for browser, model, and service connections crossing trust boundaries. Encrypt persistent sensitive data and backups, including evidence, authentication material, and model credentials. Protect deployment keys outside ordinary database exports. Model keys are available only to the gateway identity.

Verification: Connection inspection, storage inspection, credential rotation, and backup restore tests demonstrate protection. No provider key reaches browser code or testing tools. Customer-managed certificates and internal trust roots are supported without globally disabling verification.

**NFR-SEC-005 Execution isolation and scope**

Testing workers shall have restricted identities, resources, filesystem access, and network destinations. They shall not inherit production credentials, host control sockets, or platform administrative access. Destination validation shall account for DNS changes, redirects, alternate address forms, and scope exclusions. Target egress and LLM egress use separate policies.

Verification: Attempts to reach excluded assets, platform control services, metadata endpoints, or unauthorized destinations are blocked. A compromised tool worker cannot change users, model profiles, or audit history. Authorized internal model access is explicitly configured rather than enabled by broad private-network access.

**NFR-SEC-006 Untrusted model and target content**

Target pages, API responses, documents, scanner output, and model output shall be treated as untrusted data. Tool actions require validated schemas and backend policy decisions. Generated text shall be safely rendered in the UI and PDF pipeline.

Verification: Prompt-injection fixtures cannot expand scope, change configuration, disclose secrets, or create executable arbitrary shell instructions. Script-bearing evidence cannot execute in a reviewer browser or report renderer. Applies to FR-TEST-002 and FR-LLM-002.

## 4 Execution control requirements

**NFR-CTRL-001 Pause semantics and timing**

An acknowledged pause request shall durably block new task dispatch. Proposed command acknowledgment is p95 within 2 seconds. Under healthy control connectivity, workers should quiesce within 30 seconds through bounded safe checkpoints or cancellation. PAUSED requires confirmation that no testing activity remains; an in-flight action may continue only while the state is PAUSING.

Verification: Observe scheduler records, worker acknowledgments, and target traffic during long-running and state-changing fixtures. Expiry of the deadline cannot force a false PAUSED label. The UI explains any worker that prevents confirmation. Applies to FR-RUN-003.

**NFR-CTRL-002 Stop semantics and timing**

An acknowledged stop request shall durably prohibit further dispatch. Proposed command acknowledgment is p95 within 2 seconds and cessation of tool activity within 60 seconds on healthy managed workers, including a proposed 10-second graceful-termination period. STOPPED requires confirmed termination and completion or expiry of bounded authorized cleanup.

Verification: Queued jobs, running processes, child processes, outstanding model responses, and worker restarts cannot resume test activity. If a worker is unreachable, the platform reports unconfirmed termination and escalates instead of claiming STOPPED. Cleanup cannot become unbounded additional testing. Applies to FR-RUN-005.

**NFR-CTRL-003 Durable control authority**

Run control shall use atomic state versions, idempotent commands, and expiring worker execution authority. Workers shall fail closed when they lose the ability to renew authority. Proposed authority expiry is 15 seconds, subject to testing against tool execution and local egress enforcement.

Verification: Partition or restart the orchestrator and workers, issue conflicting commands, and replay stale messages. Old authority cannot dispatch new work. Stop takes precedence over pause or resume. No model response can independently change run authority.

**NFR-CTRL-004 Shared budgets and side effects**

The system shall enforce target-level budgets across all workers and serialize conflicting state changes. A proposed initial HTTP limit is 5 requests per second per approved origin with burst 5, adjustable under the rules of engagement. Any approved network-discovery module needs separately defined connection or packet limits.

Verification: Parallel workers collectively remain within configured token-bucket limits. Expired windows and exhausted budgets prevent further tests. GET requests are not presumed harmless; scenario side effects determine controls. Unknown outcomes of non-idempotent operations are reconciled before retry.

## 5 Correctness and assessment quality

**NFR-QUAL-001 Deterministic scoring**

CVSS calculations shall match approved FIRST reference cases for valid supported vectors. Invalid or internally inconsistent vectors shall be rejected. All 25 business-risk matrix cells, configured bands, and consequence overrides shall produce the approved policy result.

Verification: Automated reference and boundary tests pass without numeric discrepancies. Store calculator and policy versions. CVSS, manual reported severity, business risk, and confidence remain separate under edits and report export. Applies to FR-SCORE-001 through FR-SCORE-004.

**NFR-QUAL-002 Supported scenario benchmark**

Before release, evaluate each supported scenario with positive and negative ground-truth fixtures. A proposed initial suite includes at least 5 positive and 5 negative cases per scenario, with proposed aggregate confirmed-finding precision of at least 95 percent and recall of at least 80 percent within supported conditions. Small samples and per-scenario outcomes must be disclosed.

Verification: Independently labelled results record true positives, false positives, and false negatives; precision is TP divided by TP plus FP and recall is TP divided by TP plus FN. Duplicate reports do not inflate recall. Any automatic confirmation on a known negative fixture blocks release until corrected or the scenario is restricted. These targets do not measure arbitrary real-world coverage.

**NFR-QUAL-003 Evidence and reproducibility**

Every confirmed finding shall have adequate, integrity-checked evidence and reproducible steps or an explicit, reviewed reason why reproduction cannot safely be repeated. Claims, observed effects, assumptions, and supported potential consequences shall be distinguished.

Verification: A reviewer reproduces eligible benchmark findings using the exported instructions and authorized fixtures. Missing evidence cannot be filled by generated prose. Confidence is a documented assessment state, not an uncalibrated probability displayed as certainty.

**NFR-QUAL-004 Coverage integrity**

Coverage shall reflect actual scenario and asset execution, prerequisites, and limitations. Neither tool success nor an empty finding list may be equated with comprehensive security verification or certification.

Verification: Missing credentials, scanner errors, skipped tests, black-box limitations, and interrupted runs produce the appropriate coverage statuses. Framework references resolve to the recorded versions, and unsupported mobile or implementation controls are not shown as verified.

**NFR-QUAL-005 Retest validity and isolation**

Retests shall preserve original evidence and assessments, operate only on selected findings and necessary bounded prerequisites, and distinguish the latest attempt from the latest validated disposition. FIXED requires evidence that the original security condition is remediated, not simply that the original request now fails for an unrelated reason.

Verification: Exercise fixed, partially fixed, still open, inaccessible, redirected, expired-session, interrupted, and inconclusive fixtures. Batch retests retain individual outcomes. Pause, stop, replay, and concurrent-attempt tests cannot falsely close findings or overwrite original records. Applies to FR-FIND-005 through FR-FIND-007.

## 6 Data integrity and lifecycle

**NFR-DATA-001 Version and concurrency integrity**

Findings, assessments, policies, and engagement configurations shall retain versions. Concurrent writes shall detect conflicts. Approved report snapshots and issued artifacts shall be immutable to ordinary application operations.

Verification: Race and rollback tests preserve both authorship and the final accepted revision. Regeneration cannot erase overrides. A restore retains original and revised evidence and assessment relationships.

**NFR-DATA-002 Evidence provenance**

Artifacts shall have integrity hashes, capture metadata, run and task references, and classification. Redacted derivatives shall reference restricted originals. Verify integrity at least before report issuance and restore reconciliation.

Verification: Altered or missing artifacts are detected and prevent unsupported final findings. Redaction does not remove the protected original without an authorized retention action. Audit records do not duplicate sensitive artifact bodies.

**NFR-DATA-003 Retention and deletion**

Retention shall be configurable by artifact class, with legal hold and auditable deletion where required. Proposed starting values are 90 days for raw evidence, 365 days for issued reports and audit records, and 30 days for rotating backups, subject to DEC-05 approval.

Verification: Expiry, hold, deletion, and backup-aging tests follow policy. Reports retain clear notices if referenced raw evidence later expires. Audit retention and historical attribution are not bypassed by account deletion; PII handling follows the approved customer policy.

## 7 Audit quality

**NFR-AUDIT-001 Completeness and attribution**

All audited business operations in FR-AUDIT-002 shall carry the actor chain, action, affected resource and asset where applicable, event time, outcome, and correlation. Security and business events are not sampled. Capture both failed and successful activity where applicable.

Verification: Reconstruct a complete engagement from provisioning through report download and retest. Every expected operation in the acceptance event inventory is present. Target request details are retrievable through execution references rather than being silently omitted.

**NFR-AUDIT-002 Durability and tamper evidence**

Application identities shall not update or delete prior audit records. Maintain durable transactional capture and a protected archive. Integrity checking shall use independently protected anchors or an equivalent mechanism; a hash chain stored only beside mutable events is insufficient protection against a privileged rewrite.

Verification: Simulated application compromise cannot edit history. Tampering, gaps, archive failure, and queue exhaustion are detected. Privileged actions and sensitive reads fail closed when durable recording is unavailable, as specified in FR-AUDIT-003.

**NFR-AUDIT-003 Time ordering and retrieval**

Store occurrence and recording time in UTC using synchronized clocks, correlation identifiers, and per-execution sequence information. Proposed searchable-event delivery is within 5 seconds of durable capture under the reference workload. Clock drift beyond the approved tolerance produces an alert.

Verification: Cross-worker events are reconstructable without assuming timestamps alone establish a total order. Filters and exports preserve event IDs and UTC values. Audit access remains permission-filtered and is itself logged.

## 8 Performance and capacity

**NFR-PERF-001 Interactive response**

Under the approved reference profile, proposed p95 backend latency is at most 2 seconds for ordinary paginated reads and metadata edits, excluding file transfer, model inference, scanning, and PDF rendering. Server error rate should remain below 1 percent, excluding deliberately rejected validation and permission requests.

Verification: Use the section 2 workload and publish p50, p95, errors, saturation, and dataset size. User feedback distinguishes accepted asynchronous work from completed work.

**NFR-PERF-002 Long running work**

Scanning, inference, and report generation shall run outside interactive request lifetimes. Proposed run-control acknowledgment is covered by NFR-CTRL. A proposed PDF-generation target is within 120 seconds for the approved report fixture, measured separately from reviewer time and artifact upload.

Verification: A slow model or renderer does not block login, run controls, or audit inspection. Queue state, retry state, and timeout are visible. Platform latency is not presented as a guaranteed total pentest duration.

**NFR-PERF-003 Bounded resources**

Workers and model calls shall have configured concurrency, memory, CPU, duration, and request or usage budgets. Storage thresholds shall warn operators before exhaustion and block new evidence-producing work when durable capture cannot be guaranteed.

Verification: Stress tests produce bounded queuing or explicit rejection, not uncontrolled process growth, missing evidence, or silent audit loss. Model usage accounting handles providers that omit token counts without fabricating values.

## 9 Reliability and recovery

**NFR-REL-001 Restart consistency**

Workflow, evidence, findings, audit events, and control state shall survive process restarts. At-least-once job delivery shall not cause duplicate logical actions; side effects require idempotency or reconciliation rather than an unsupported exactly-once guarantee.

Verification: Inject crashes before and after tool execution, persistence, and acknowledgment. Completed results survive. Unknown state-changing outcomes remain blocked for review. A restored PAUSED or STOPPED run does not restart testing automatically.

**NFR-REL-002 Dependency failure**

Model, database, storage, and worker failures shall produce explicit degraded or unavailable states. Model retries are bounded, honor cancellation, and remain inside the selected data boundary. Local-model failure cannot trigger cloud fallback.

Verification: Timeout and outage fixtures preserve evidence, stop unsafe dispatch, expose a recovery path, and maintain accurate run status. Partial results remain readable when dependencies permit safe access.

**NFR-REL-003 Backup and restore**

Backups shall cover the database, evidence, issued reports, audit archive, system prompt versions and releases, configuration, and necessary recovery keys under separate protection. Proposed recovery objectives are RPO 24 hours and RTO 4 hours for the reference installation. Perform a restore drill before release and at an approved recurring interval.

Verification: Restore into an isolated environment and validate object references, report hashes, audit continuity, account recovery, and run reconciliation. Document what work can be lost under the RPO. No automatic target traffic occurs during restore.

**NFR-REL-004 Availability objective**

A proposed application availability objective is 99.5 percent during agreed operating windows, excluding approved maintenance. The customer operating environment and approved dependency health are explicit assumptions. High availability clustering is not an MVP prerequisite.

Verification: Define probes, operating windows, maintenance records, and incident calculation before measuring the objective. Model inference availability is measured separately from the ability to access existing results and control runs.

## 10 Model portability and privacy

**NFR-LLM-001 Contract compatibility**

Agent code shall use only the gateway interface. The initial external contract is OpenAI-compatible Chat Completions. Provider support shall be determined by capability tests, not endpoint naming. Structured output validation remains mandatory even when a provider advertises schema support.

Verification: Exercise one approved local and one approved cloud profile through the same fixtures, including invalid outputs, refusals, tool proposals, truncation, timeouts, and cancellation. Validate task quality as well as protocol shape before assigning an agent role.

**NFR-LLM-002 Explicit data boundary**

Outbound content shall be classified, minimized, and checked against the selected profile policy. Cloud inference is optional and disabled until configured. Default external telemetry is off. No unapproved model, analytics, embedding, or hosted orchestration dependency is required for local operation.

Verification: Inspect egress during a full local-model assessment and during cloud-profile tests. Local operation produces no vendor-bound traffic. Cloud tests send only approved inference content and retain platform state on-premises. Network controls reinforce the gateway policy.

**NFR-LLM-003 Reproducibility limits**

Store profile, model identifier or available revision, system prompt version and content hash, system prompt release manifest, agent and LLM profile assignment, settings, and relevant validated output for assessment traceability. Runtime user and task inputs remain separate evidence under the configured retention policy. Model determinism is not assumed. Issued reports shall use stored approved records rather than fresh inference.

Verification: Provider changes create new provenance. The same approved snapshot preserves substantive report content even when model behavior changes. Raw private reasoning traces are not required for auditability.

### 10.1 System prompt governance quality

**NFR-PROMPT-001 Administrative isolation**

System prompt management and user access to system instruction bodies shall require the Administrator role at every access boundary. Only the gateway execution service may resolve pinned bodies under a separate read-only identity for inference. Audit logs shall record actor, action, system prompt or release ID, agent and model assignment, version, time, outcome, and change reason without exposing unrestricted bodies. System prompt data shall remain on-premises except for content deliberately sent to the selected approved inference endpoint.

Verification: Direct API, object-reference, storage, and role-change tests deny non-Administrator management and body retrieval. Authorized metadata remains available for finding provenance. User or task messages do not create, edit, or activate system prompt versions. A failed audit write blocks privileged system prompt changes. Applies to FR-PROMPT-001 through FR-PROMPT-004.

**NFR-PROMPT-002 Immutable releases and concurrency**

Published system instructions and release manifests shall be immutable and integrity-checked. Activation shall be atomic, history-preserving, and consistent under concurrent updates. Executions shall resolve the agent and LLM profile assignment for every model call through their pinned manifest, including retries, resumption, and reporting jobs.

Verification: Concurrent publish and activation, rollback, worker restart, and model-call tests produce no mixed release. Active and paused runs retain their original versions after activation. Missing or altered versions fail closed. Backup and restore recover referenced versions and manifests. Applies to FR-PROMPT-002, FR-PROMPT-004, and FR-PROMPT-005.

**NFR-PROMPT-003 Validation and regression control**

System prompt publication and activation shall require successful trusted-variable and output-contract validation and approved regression fixtures for affected agent roles and LLM profiles. Evaluations shall record dataset, system prompt, model, configuration, and outcome; they shall respect inference data boundaries and never execute target tools. The gateway shall preserve the provider's system-instruction semantics separately from runtime user messages, evidence, and tool outputs. Results do not establish that a model is deterministic or universally correct.

Verification: Broken-variable, unsafe-expression, invalid-output, unsupported-system-role, prompt-injection, and quality-regression fixtures block the relevant transition. An eligible previous release can be restored as an audited activation without altering historical runs. Runtime user or target content cannot replace the pinned system instructions, and backend scope, scoring, permission, and cancellation controls remain effective under adversarial system prompts. Applies to FR-PROMPT-003 through FR-PROMPT-005.

## 11 Deployment maintainability and operations

**NFR-DEPLOY-001 On premises package**

The platform shall install and operate on customer infrastructure using documented, versioned packages. The supported host OS and architecture require DEC-01 approval. A proposed first support target is a Linux x86-64 container host, with application services and isolated workers on the customer network.

Verification: A clean installation, local authentication, local-model assessment, and PDF export succeed with external vendor access blocked and a local authorized test target. Cloud inference requires only configured egress, not relocation of the platform.

**NFR-DEPLOY-002 Controlled updates**

Pin application, tool, template, framework catalogue, and calculator versions per release and run. Support administrator-controlled update imports and documented migrations. Running assessments shall not change executable content through unattended template downloads.

Verification: Reproduce installed versions from release metadata, verify package integrity and provenance, perform a migration rehearsal, and demonstrate rollback or documented restore. Offline package transfer is supported; fully air-gapped testing of public targets is not implied.

**NFR-OPS-001 Health and alerts**

Expose health, queue depth, worker authority, run-control state, audit backlog, storage capacity, model failures, and backup status. Distinguish operational logs from audit records and restricted evidence. Correlation identifiers connect these views.

Verification: Inject each critical failure and confirm an on-premises administrator can identify affected engagements and the required action. Unconfirmed worker termination and audit persistence failure generate prominent alerts without requiring an external notification service.

**NFR-OPS-002 Maintainable interfaces**

Authentication, authorization, audit capture, scoring, gateway access, and tool execution shall have explicit interfaces and automated contract tests. Keep the implementation modular; separate deployment of every logical module is not required.

Verification: Agents cannot import provider clients or execute tools outside approved interfaces. API schemas, migrations, operational procedures, and configuration meanings are documented. A dependency inventory and license review accompany release packaging.

## 12 Usability and report quality

**NFR-UX-001 Clear operational state**

The UI shall distinguish request acknowledgment from confirmed PAUSED or STOPPED states, and expose blocked, failed, incomplete, and provisional outcomes in plain language. Destructive termination should have a concise confirmation explaining that the run cannot resume; pause does not need an extra confirmation.

Verification: Representative users can identify whether testing is still active, why progress stopped, and what can happen next. All controls remain keyboard accessible with visible focus and no reliance on color alone. No statement of complete accessibility conformance is implied without a dedicated audit.

**NFR-UX-002 Assessment transparency**

Users shall be able to distinguish generated, calculated, manually overridden, and reviewed assessments. Display severity, business risk, and confidence separately. Reasons and evidence shall be reachable from the assessment view without inspecting raw technical logs.

Verification: Review tasks correctly identify current ratings, original recommendations, override authors, stale decisions, and provisional business context. Unauthorized users cannot edit by direct requests.

**NFR-REPORT-001 PDF integrity and readability**

PDFs shall contain selectable text, readable tables, clear evidence captions, version and page identification, working reference links where applicable, and consistent section order. No clipped text, overlapping elements, broken images, or exposed report secrets are acceptable.

Verification: Run structural checks and render every page of representative complete, partial, long-finding, no-finding, and retest reports. Inspect the rendered pages. Automated field checks compare scores, overrides, coverage, and status against the approved snapshot.

**NFR-REPORT-002 Export isolation**

Report generation shall use stored approved content and local rendering. Target-supplied HTML or links cannot cause uncontrolled script execution, network retrieval, or data disclosure during rendering. Downloads require current permission and audit recording.

Verification: Malicious evidence fixtures cannot read local files or contact arbitrary endpoints. A later finding edit does not change an issued artifact. Preview and partial assessment labels remain visible on exported pages.

## 13 Release evidence and exceptions

The acceptance register shall map each FR and NFR ID to verification evidence. Mandatory properties cannot be waived by labelling a test inconclusive. Proposed numerical targets must be approved, revised, or explicitly deferred before release; their status must not be silently treated as passed.

Any approved exception shall record its owner, scope, rationale, compensating measure, expiry, and affected product claim. Unresolved unauthorized access, scope escape, false execution state, silent cloud routing, incorrect scoring, missing audit attribution, evidence corruption, or misleading issued reports are release blockers.

Maintain the approved baseline, benchmark results, security test results, finding-retest results, provider capability results, system prompt evaluation and rollback results, PDF inspection record, restore drill, operating procedures, and exception register with the release. Standards and integration references are listed in FRD section 15.
