# AI Penetration Testing Platform Product Requirements Document

Version 1.1 | 4 November 2026 | MVP requirements baseline for review

Audience: Product owner, engineering lead, security lead, and acceptance reviewers.

Revision 1.1 expands finding-based retesting and adds Administrator-only system prompt management for each agent and configured LLM profile, with validation, versioning, activation, and rollback. User prompts and runtime task inputs are outside this management feature.

## 1 Product purpose

Build an on-premises AI-assisted penetration testing platform for authorized black-box assessment of web applications and exposed HTTP APIs. The platform coordinates specialist agents, executes controlled tests through established tools, validates findings against evidence, and produces an editable assessment followed by a versioned PDF report.

The product must help analysts explain what was tested, what was found, how the result was verified, why it matters, and how to remediate it. Users retain control over execution and reported severity. Platform data and execution remain on-premises; model inference may use an approved local or cloud endpoint.

This PRD defines product outcomes and scope. The FRD defines observable behavior and acceptance criteria. The NFRD defines quality attributes and verification targets. Requirement IDs provide traceability across the three documents.

## 2 Product decisions

The following decisions establish the MVP boundary. They supersede cloud-hosted platform and external identity-provider proposals.

| Decision | MVP requirement |
| --- | --- |
| Platform location | Run the application, agents, workflow state, workers, database, evidence, audit storage, and report generation on-premises. |
| Model location | Support local and approved cloud LLM endpoints through an OpenAI-compatible interface. No silent cross-boundary fallback. |
| Login | Local username and password followed by mandatory TOTP, with secure server-side browser sessions. |
| Initial roles | Administrator, Analyst, Reviewer, and Viewer, with project or engagement access checks. |
| Test targets | Web applications and exposed HTTP APIs only. |
| Assessment mode | External black-box assessment with no source code, internal configuration, or internal network access. |
| User control | Authorized users can pause, resume, stop, edit findings, and override reported severity with attribution. |
| Retesting | Analysts can retest one finding or selected findings, preserving original evidence and recording each attempt. |
| System prompt management | Only Administrators manage system instructions assigned to each agent and approved LLM profile. Executions pin immutable versions. |
| Assessment outputs | Separate CVSS 4.0 technical severity, business risk, and evidence confidence. |
| Business risk | Customer-approved 5 by 5 likelihood and impact matrix within an ISO 31000-aligned risk process. |
| Reporting | Reviewed, versioned PDF containing scope, coverage, findings, scoring rationale, remediation, and retest status. |

Black-box does not necessarily mean anonymous. The default profile starts anonymously and may use authorized self-registration. Customer-provided accounts or API specifications must be explicitly disclosed as additional inputs in an authenticated external or specification-assisted profile. These profiles still exclude internal implementation access.

## 3 Problem and users

Tool output alone is difficult to turn into a dependable penetration testing report. Analysts must select applicable tests, control execution, validate alerts, collect reproducible evidence, assess impact, and explain coverage limits. Multiple agents can accelerate independent work, but also introduce duplicate findings, inconsistent scores, ungrounded conclusions, and conflicting actions against shared accounts.

| User | Need | Main responsibilities |
| --- | --- | --- |
| Administrator | Operate a controlled on-premises installation. | Manage accounts, permissions, model profiles, system prompts, policies, and operational settings. |
| Analyst | Run assessments and investigate credible findings. | Configure authorized engagements, control tests, review evidence, edit findings, and adjust assessments. |
| Reviewer | Issue defensible results. | Review findings and overrides, approve report snapshots, and evaluate retest results. |
| Viewer | Understand authorized results. | Read permitted engagements, findings, evidence, and issued reports. |

An administrator is not automatically authorized to test a target. Engagement authorization and target scope remain separate from platform administration. Role combinations may be assigned to one user; a mandatory two-person approval process is not an MVP requirement.

## 4 Product objectives and success measures

| Objective | Desired outcome | Release evidence |
| --- | --- | --- |
| PRD-01 Controlled access | Only authenticated and authorized users access protected resources. | Authentication, role, and object-access acceptance tests. |
| PRD-02 Controlled execution | Every test respects recorded authorization, scope, budgets, and run controls. | Scope escape, concurrency, pause, resume, and stop tests. |
| PRD-03 Credible assessment | Findings are supported by evidence and accurately mapped to applicable tests. | Ground-truth benchmark and reviewer validation. |
| PRD-04 Explainable prioritization | Technical severity and business risk are independently justified and editable. | CVSS reference checks, risk-policy checks, and override history. |
| PRD-05 Useful reporting | Reports reproduce reviewed results and communicate coverage honestly. | Structured completeness and visual PDF checks. |
| PRD-06 Accountable operation | User, agent, service, and tool actions are attributable. | End-to-end audit reconstruction. |
| PRD-07 Model portability | Local and cloud inference use the same agent-facing contract. | Provider compatibility and data-boundary tests. |
| PRD-08 Local operation | The platform operates on-premises without a required hosted control plane. | Installation, recovery, and local-model deployment tests. |
| PRD-09 System prompt governance | Agent and LLM system instructions are restricted, validated, versioned, and traceable to executions. | Administrator access, version pinning, activation, and rollback tests. |

Proposed quantitative quality gates are defined in the NFRD. They are engineering targets for review, not measured results or commitments to assessment completeness. Product adoption measures after pilot deployment should include analyst review time, accepted-finding rate, override frequency, and time from assessment start to report approval. Pilot baselines are needed before setting improvement percentages.

## 5 MVP scope

### 5.1 Included capabilities

- Local account provisioning, username and password login, mandatory TOTP, recovery, session management, and the four initial roles.
- Projects and engagements with approved targets, exclusions, authorization records, access profiles, testing windows, budgets, and business context.
- An Orchestrator Agent coordinating discovery, specialist testing, validation, risk assessment, and reporting roles.
- A versioned catalogue of externally verifiable web and API scenarios, using WSTG methods and relevant ASVS mappings.
- Structured adapters for a small initial toolset: ZAP, Playwright, reviewed Nuclei templates, a controlled HTTP client, and limited Nmap discovery when separately in scope.
- Application and API discovery; bounded tests for configuration, authentication, sessions, authorization, input handling, and selected business flows.
- Controlled validation, evidence collection, deduplication, cleanup tracking, and finding review.
- Deterministic CVSS 4.0 calculation and a configurable business-risk matrix with customer-approved definitions.
- Versioned severity overrides and finding edits with reasons and reviewer visibility.
- Pause, resume, stop, progress visibility, partial-assessment handling, and retesting of one finding or selected findings without rerunning the full assessment.
- Complete activity attribution, protected audit access, and versioned PDF exports.
- Local or approved cloud model inference through one OpenAI-compatible gateway.
- An on-premises system prompt library with Administrator-only editing, validation, version comparison, publication, agent and LLM profile assignment, release activation, rollback, and retirement.

The initial catalogue should contain approximately 15 to 20 carefully validated scenarios. The exact list is a proposed release-planning decision, not a claim of complete WSTG or ASVS coverage. Each scenario must have prerequisites, evidence expectations, side-effect controls, and acceptance fixtures.

### 5.2 Excluded capabilities

Native Android and iOS testing, MASVS verification, internal network assessments, source-code review, cloud-infrastructure assessments, social engineering, physical testing, and denial-of-service campaigns are excluded. Destructive actions, live financial effects, and unrestricted exploitation are outside the default execution profile.

Also excluded are a cloud-hosted platform, SaaS billing, mandatory enterprise SSO, a public registration portal, unrestricted model-generated shell execution, and a general-purpose autonomous exploitation engine. A fully air-gapped installation is not promised when the engagement requires public targets or cloud inference.

MASVS and MASTG are future mobile references. They must not appear as completed MVP verification. Framework mapping does not establish certification or comprehensive compliance.

## 6 User journey

### 6.1 Access and preparation

An administrator provisions users. A user sets a password, enrolls TOTP, and signs in. An analyst creates an engagement, records authorization, selects targets and exclusions, chooses a supported model profile, and defines the execution window and limits. Business context identifies important workflows, sensitive data, impact thresholds, and a risk owner.

### 6.2 Assessment execution

The platform checks readiness and creates a test plan. Discovery reveals candidate pages, endpoints, parameters, and workflows. The orchestrator selects applicable scenarios and schedules independent work in parallel. Scope enforcement and shared budgets apply to every worker. Tests sharing state-changing accounts or data use coordination locks.

Candidates move into validation. Unsupported claims remain rejected or inconclusive. Evidence collection and report drafting proceed as confirmed results become available.

### 6.3 Intervention

An authorized analyst can request pause or stop from the live engagement screen. The interface distinguishes the request from confirmed worker state. Pause preserves checkpoints for resumption. Stop ends that run permanently while retaining collected evidence and tracking outstanding cleanup. A new linked run is required to continue a stopped assessment.

### 6.4 Review and reporting

An analyst reviews findings and scoring explanations, changes metrics or ratings where justified, and records reasons. A reviewer approves a report snapshot. The platform exports that snapshot to PDF. Subsequent edits or retests create another report version; issued reports remain unchanged.

### 6.5 Finding based retesting

An analyst selects one finding or a set of findings from an engagement, records remediation context, and starts a linked retest run. The platform rechecks scope, authorization, access, and the original success criteria. It executes the selected checks and necessary bounded prerequisites, rather than the full catalogue. Each finding retains attempt history, original and new evidence, version differences, and the latest validated disposition. Interrupted or inconclusive attempts cannot mark a finding fixed. Retest runs use the same pause, resume, stop, and audit controls as initial runs.

### 6.6 System prompt management

An Administrator selects an agent role and approved LLM profile, edits its system instructions, compares versions, and validates behavior against controlled fixtures. The instructions define the agent's responsibilities, reasoning and output requirements, and operating rules. Published versions are immutable. A system prompt release groups the required agent and model assignments into a consistent version set that the Administrator can activate or roll back. One published version may be reused for compatible profiles. Active runs retain their pinned release; updates apply to new executions.

This feature does not manage user prompts. Targets, evidence, business context, and user task instructions remain runtime inputs, separate from system instructions. They cannot become published system prompt content through normal use. System prompt changes cannot alter backend scope, permissions, scoring rules, or run controls. Analysts, Reviewers, Viewers, and agents cannot manage system prompts.

## 7 Assessment and evidence principles

### 7.1 Technical severity and business risk

CVSS 4.0 describes technical vulnerability severity. The platform must retain the vector, calculated score, nomenclature, and per-metric rationale. Missing justification makes an assessment provisional. Tool-provided CVSS 3.1 scores cannot be directly relabelled as 4.0 scores.

Business risk is a distinct assessment of a stated business scenario over an agreed time horizon. The customer approves likelihood definitions, impact criteria, matrix bands, consequence overrides, and treatment expectations. ISO 31000 does not prescribe a particular 5 by 5 matrix or score thresholds. The product supports an aligned process rather than claiming ISO certification.

Users can change CVSS inputs, manually override reported severity, or adjust business likelihood and impact. These are different operations and must remain distinguishable in the interface, history, and reports.

### 7.2 Validation and coverage

Every confirmed finding needs sufficient evidence for its claim, expected versus actual behavior, ordered reproduction steps, prerequisites, impact, and remediation. Observed behavior and supported potential consequences must be distinguished. AI agreement and a scanner alert alone do not establish confirmation.

Coverage is tracked for each applicable test and target combination. Not tested, inconclusive, not applicable, tested with an issue, and tested with no observed issue are different outcomes. Absence of findings is not proof that the application is secure.

### 7.3 Business logic

The platform records workflow states, roles, preconditions, and rules. Rules are marked observed, inferred, or customer-confirmed. Tests can explore skipped steps, repeated actions, and cross-account access when prerequisites are available. A suspected violation of an inferred rule requires confirmation of intended behavior before being reported as a confirmed business-rule defect.

## 8 Product surfaces

| Surface | Main content and controls |
| --- | --- |
| Login and account | Password and TOTP login, enrollment, recovery, and session actions. |
| Engagement dashboard | Scope, readiness, progress, active tasks, budgets, and pause or stop controls. |
| Coverage view | Tests and assets, applicability, outcomes, limitations, and framework references. |
| Finding workspace | Evidence, reproduction, remediation, scoring, overrides, review, selected-finding retest, and before-and-after attempt history. |
| Reports | Draft preview, approval, version history, and PDF download. |
| Audit explorer | Actor, action, affected resource and asset, time, outcome, and correlation filters. |
| Administration | Users, access, model profiles, system prompt library and releases, risk policies, catalogue versions, and operating settings. |

### 8.1 Delivery risks

| Risk | Product response | Accountable role |
| --- | --- | --- |
| Unsupported AI conclusions | Evidence-based validation, explicit uncertainty, and reviewer control. | Security lead |
| Incomplete black-box access | Coverage status and limitations in the workspace and report. | Analyst |
| Conflicting or excessive test traffic | Shared budgets, resource locks, and backend-enforced controls. | Engineering lead |
| Cloud disclosure of restricted content | Explicit model profiles, outbound policy, redaction, and no silent fallback. | Administrator |
| Misleading risk ratings | Separate technical and business assessment, approved criteria, and override history. | Risk owner |
| System prompt changes that disrupt assessments | Administrator-only publishing, validation fixtures, immutable releases, run pinning, and rollback. | Administrator and security lead |

## 9 Release acceptance and traceability

| Product objective | FRD families | NFRD families |
| --- | --- | --- |
| PRD-01 | FR-AUTH, FR-ACCESS | NFR-SEC, NFR-UX |
| PRD-02 | FR-ENG, FR-RUN, FR-TEST | NFR-CTRL, NFR-REL, NFR-SEC |
| PRD-03 | FR-TEST, FR-FIND | NFR-QUAL, NFR-DATA |
| PRD-04 | FR-SCORE | NFR-QUAL, NFR-DATA |
| PRD-05 | FR-REPORT | NFR-REPORT, NFR-UX |
| PRD-06 | FR-AUDIT | NFR-AUDIT, NFR-OPS |
| PRD-07 | FR-LLM | NFR-LLM, NFR-SEC |
| PRD-08 | FR-OPS | NFR-DEPLOY, NFR-REL, NFR-OPS, NFR-PERF |
| PRD-09 | FR-PROMPT, FR-LLM, FR-AUDIT | NFR-PROMPT, NFR-SEC, NFR-AUDIT |

Release requires all mandatory functional acceptance criteria and all approved non-functional gates to pass. Blocking defects include unauthorized access or execution, false stopped or paused states, missing audit attribution, evidence loss, incorrect CVSS calculation, silent cloud routing, and reports that misrepresent coverage or manual overrides.

## 10 Delivery and review decisions

Recommended delivery sequence is foundation and access; controlled workers and evidence; curated tests and validation; scoring and review; PDF reporting and retesting; then benchmark and operational acceptance. The specific language, workflow engine, database product, and deployment packaging are implementation decisions subject to the requirements.

| Decision ID | Review item | Proposed owner |
| --- | --- | --- |
| DEC-01 | Supported on-premises operating environment and capacity profile. | Engineering and operations |
| DEC-02 | Initial test catalogue, permitted side effects, and target budgets. | Security lead and product owner |
| DEC-03 | Customer risk definitions, thresholds, horizon, and treatment rules. | Risk owner |
| DEC-04 | Session timeouts, login controls, and recovery administration policy. | Security lead |
| DEC-05 | Evidence, report, audit, backup retention, and deletion policy. | Customer administrator and risk owner |
| DEC-06 | Approved model endpoints, capability requirements, and permitted outbound content. | Customer administrator and security lead |
| DEC-07 | Performance, recovery, and assessment-quality targets proposed in the NFRD. | Engineering and acceptance reviewers |

Unresolved values must be visible in configuration readiness checks or release planning; they must not be silently filled by agents. Existing approved settings are reused without requiring confirmation for every ordinary test action.

## 11 Reference baseline

The FRD contains the technical reference register. Key sources are FIRST CVSS 4.0, OWASP WSTG and ASVS, ISO 31000 risk-management guidance, IEC 31010 assessment techniques, PTES for the overall engagement lifecycle, and NIST SP 800-115 for assessment planning. These guide the product; its supported test catalogue and recorded coverage define the actual assessment delivered.
