# AI-Assisted Pentest Platform

On-premises AI-assisted penetration testing platform for authorized external black-box assessment of web applications and exposed HTTP APIs. The implementation follows `PRD.md`, `FRD.md`, `NFRD.md`, and `Development_Guide.md`.

## Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, layered as `database → repository → usecase → controller` with constructor injection and a composition root.
- **Frontend:** SvelteKit 3 + TypeScript SPA (`ssr = false`, `adapter-static`) using **Bun** for installation, scripts, tests, and builds.
- **Evidence:** S3-compatible object storage. The default Compose file uses LocalStack S3; replace `S3_ENDPOINT` with MinIO or another approved S3 endpoint without changing application code.
- **PDF:** ReportLab renders selectable-text PDFs from approved immutable report snapshots.
- **Inference:** OpenAI-compatible Chat Completions gateway with explicit profiles, structured-output validation, and no automatic cloud fallback. A deterministic mock endpoint is included for local use.
- **Tools:** Controlled HTTP client is active. ZAP, Nuclei, Playwright, and Nmap adapters are allowlisted and disabled by default (`TOOLS_ENABLED=false`).
- **Agentic workflow:** A durable backend scheduler owns task state, leases, budgets, locks, cancellation, and run transitions. Orchestrator, Discovery, Web Testing, API Testing, Authorization/Business Logic, Validation, Risk Assessment, and Reporting roles use pinned prompts and structured contracts through the shared LLM gateway. The bundled mock model profile exercises the full local pipeline.

## Repository layout

```text
backend/
  src/pentest_platform/
    domain/        # entities, errors, access policy, run state machine, scoring
    ports/         # repository, unit of work, security, audit, LLM, tools, reporting
    db/            # SQLAlchemy schema and session factory
    repositories/  # SQLAlchemy repository and unit of work
    usecases/      # auth, access, engagements, runs, testing, findings, scoring,
                   # prompts, audit, reports, admin
    controllers/   # FastAPI routers, dependency wiring, schemas
    adapters/      # Argon2/TOTP, hash-chain audit, S3/local evidence, PDF, LLM, tools
    bootstrap/     # settings, composition root, app factory, seed data
    workers/       # durable agent scheduler and parallel task execution
  tests/unit/{usecases,controllers}
  scripts/         # architecture, inventory, coverage gates, migrations
frontend/
  src/lib/{api,components,stores}
  src/routes/      # SPA routes
  tests/unit/{components,routes,api,stores}
  tests/coverage-map.json
deploy/            # nginx, mock LLM, backup/restore, healthcheck
.github/workflows/ # quality, CodeQL/Trivy security gates
```

## Quick start

Use the root entrypoint to build, start, health-check, and activate every service:

```sh
./start.sh
```

It creates `.env` from `.env.example` when missing, starts `db`, `s3`, `mock-llm`, `backend`, `worker`, and `frontend`, then waits for health before printing the UI/API URLs.

```sh
./start.sh --bootstrap   # start + prompt for the initial administrator
./start.sh --no-build    # start using existing images
./start.sh --logs        # follow logs
./start.sh --status      # show service status
./start.sh --stop        # stop services, retain volumes
./start.sh --reset       # stop services and delete volumes
```

Change `SECRET_KEY`, `AUDIT_ANCHOR_KEY`, `BOOTSTRAP_TOKEN`, and storage credentials in `.env` before production use. Open `http://localhost:8080`.

1. Bootstrap the initial administrator with the configured `BOOTSTRAP_TOKEN`:

```sh
curl -X POST http://localhost:8080/api/v1/auth/bootstrap \
  -H 'Content-Type: application/json' \
  -d '{"bootstrap_token":"change-me-bootstrap-token","username":"admin","password":"correct horse battery"}'
```

2. Sign in, enroll TOTP, and store the recovery codes.
3. Create an engagement with valid authorization, scope, and testing window.
4. Start a run. The worker executes the approved scenario catalogue.
5. Add evidence, validate findings, score CVSS 4.0/business risk, review, approve a snapshot, and render the PDF.

The bootstrap administrator receives `Administrator`, `Analyst`, and `Reviewer` roles so a fresh installation can complete the approved-snapshot flow. Two-person approval remains optional policy. Additional users can be provisioned without a public signup surface.

## Local development

Backend:

```sh
cd backend
uv sync --extra dev
uv run uvicorn pentest_platform.main:app --reload
```

By default the backend uses SQLite and local evidence storage. To use PostgreSQL/S3, set `DATABASE_URL` and the `S3_*`/`EVIDENCE_BACKEND` variables from `.env.example`.

Frontend:

```sh
cd frontend
bun install
bun run dev
```

Vite proxies `/api` to `http://localhost:8000`. The production build is a static SPA served by nginx with a separate `/api` proxy so API errors are never rewritten to `index.html`.

## Verification commands

Backend:

```sh
cd backend
uv run python scripts/check_architecture.py
uv run python scripts/check_test_inventory.py
uv run ruff check src tests
uv run mypy src
uv run pytest tests/unit/usecases tests/unit/controllers \
  --junitxml=artifacts/backend-unit.xml \
  --cov=pentest_platform.usecases \
  --cov=pentest_platform.controllers \
  --cov-branch --cov-report=json:artifacts/backend-coverage.json \
  --cov-report=term-missing
uv run python scripts/check_coverage.py artifacts/backend-coverage.json
```

Frontend:

```sh
cd frontend
bun run lint
bun run check
bun run test:inventory
bun run test:unit
bun run build
```

Selected coverage floors: backend 80% statements / 60% branches; frontend 85% statements / 50% branches / 75% functions / 85% lines. The mandatory per-component/page test inventory is 100%.

## Agentic architecture

- `AgentExecutionUsecase` loads an isolated task context, resolves the pinned prompt release and model profile, applies the execution gate, runs approved tools through isolated workers, validates structured agent output, and persists results/proposals.
- `AgentSchedulerUsecase` owns queued-run transition, task claiming with leases, expired-lease recovery, pause/stop reconciliation, and bounded parallel execution.
- `AgentProposal` records every proposed task, asset, candidate, validation verdict, risk input, or report draft with its approval/denial reason.
- `AssetRecord`, `AgentTaskResult`, `ResourceLock`, and `BudgetLedger` provide the run-scoped workspace, evidence-linked results, resource ownership, and shared request/model/task/iteration budgets.
- Validation is mandatory before risk assessment and report inclusion. Risk Assessment can only propose inputs; deterministic scoring calculates the result. Reporting can only create a preview draft; Reviewer approval remains required.
- Agent activity is exposed at `GET /api/v1/runs/{run_id}/agents` and rendered in the engagement detail **Agent Activity** panel.

## Security workflows

`.github/workflows/security.yml` runs on every pull request:

- **CodeQL SAST** for Python and JavaScript/TypeScript with a HIGH/CRITICAL gate (`security-severity >= 7.0`) that exits non-zero.
- **Trivy SCA** on the repository with `CRITICAL,HIGH` and `exit-code: 1`.
- **Trivy container scan** for both backend and frontend images with `CRITICAL,HIGH` and `exit-code: 1`.

Each job fails independently. For merge blocking, mark all three jobs as required status checks in the repository branch protection/ruleset configuration.

## Security and operational notes

- Change all development secrets before deployment. Use TLS at the reverse proxy and set `COOKIE_SECURE=true`. Evidence is encrypted at rest with a key derived from `SECRET_KEY` unless `EVIDENCE_ENCRYPTION_KEY` is provided; changing the key makes existing evidence unreadable, so protect and back it up separately.
- Passwords use Argon2id; TOTP secrets are encrypted; recovery codes are stored as hashes and consumed once.
- Sessions are server-side and HTTP-only. Mutations require a CSRF double-submit token.
- Audit events are append-only, hash-chained, and use a separately protected HMAC anchor.
- System prompt bodies are Administrator-only. Published versions are immutable, releases are activated atomically, and runs pin the active release.
- External scanning tools remain disabled until explicitly configured. The HTTP client enforces recorded targets/exclusions and bounded timeouts.
- Backups: `deploy/backup.sh`. Restore: `deploy/restore.sh <backup-directory>`. Reconcile run authority and evidence references before resuming execution.
- Live scanner effectiveness, real model quality, browser cookie behavior, external target authorization, PDF visual inspection, and restore drills require operator-run acceptance fixtures in the deployment environment.

## Requirement coverage

- Auth, TOTP, recovery, sessions, CSRF, throttling, and account lifecycle: `FR-AUTH-*`.
- Roles, backend authorization, and engagement membership: `FR-ACCESS-*`.
- Engagement scope, readiness, authorization, and plan generation: `FR-ENG-*`.
- Versioned run state, idempotent pause/resume/stop, worker leases, cleanup: `FR-RUN-*`.
- Versioned scenario catalogue, controlled tools, coverage statuses: `FR-TEST-*`.
- Finding lifecycle, evidence integrity, versioned edits, selected-finding retests: `FR-FIND-*`.
- Deterministic CVSS 4.0 and versioned 5×5 business risk: `FR-SCORE-*`.
- OpenAI-compatible gateway, structured outputs, explicit data boundary, provenance: `FR-LLM-*`.
- Administrator-only system prompt library, immutable releases, pinning, rollback: `FR-PROMPT-*`.
- Hash-chained audit, filtered explorer, export: `FR-AUDIT-*`.
- Immutable report snapshots and PDF export: `FR-REPORT-*`.
- On-premises configuration, health, backup/restore: `FR-OPS-*`.
- Multi-agent orchestration, role contracts, handoffs, isolated task context, execution gate, concurrency, bounded failure handling, and retest routing: `FR-AGENT-001` through `FR-AGENT-008`.
