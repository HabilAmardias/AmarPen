# AI Penetration Testing Platform Development Guide

Version 1.0 | 4 November 2026 | Companion to the PRD FRD and NFRD version 1.1

Audience: Backend developers, frontend developers, technical leads, QA, and code reviewers.

## 1 Purpose and mandatory engineering rules

This guide defines how to implement the on-premises web and API penetration testing MVP. The PRD defines product scope, the FRD defines functional behavior, and the NFRD defines quality attributes. This guide adds mandatory architecture, dependency injection, frontend, and unit-testing rules. Existing requirements remain in force, including local password and TOTP authentication, finding-based retests, Administrator-only system prompt management, audit attribution, and backend-enforced pause and stop controls.

The frontend technology is now fixed as SvelteKit with TypeScript in SPA mode. Python with FastAPI is the recommended backend implementation baseline carried forward from the requirements discussion; its exact supported versions must be pinned during repository setup. The layer boundaries and test obligations below apply even if an approved backend implementation choice changes.

| Rule | Required outcome |
| --- | --- |
| DEV-01 Backend layers | Build the database, repository, usecase, and controller layers with explicit boundaries. |
| DEV-02 Dependency injection | Supply collaborators through constructors and a composition root; application rules depend on interfaces. |
| DEV-03 Backend unit tests | Every usecase and controller has meaningful unit tests, including failure and permission paths. |
| DEV-04 Frontend architecture | Build a SvelteKit SPA served on-premises, calling the separate backend over HTTP. |
| DEV-05 Frontend unit tests | Every shipped component and page has unit tests; include layouts and error views. |
| DEV-06 HTTP isolation | Mock every frontend HTTP call in unit tests and fail unexpected requests. |
| DEV-07 Passing tests | All required backend and frontend unit tests must pass before merge or release. |
| DEV-08 Verification evidence | Attach actual test results, source revision, and inventory checks to the change. |

The guide defines required implementation gates. A test result is established only by executing the relevant suite against the implementation revision and preserving its output. Document review, example commands, and the presence of test files do not establish a passing application suite.

## 2 Repository and module structure

Keep a modular backend and separate frontend, worker, and deployment entry points. A separate deployed service for every module is not required. Use one repository structure consistently; the following is the recommended baseline.

```text
backend/
  src/pentest_platform/
    domain/             Entities and business errors
    ports/              Repository and external service interfaces
    db/                 Schema models migrations and session factory
    repositories/       Persistence implementations
    usecases/           Application actions and policy decisions
    controllers/        HTTP routes schemas and response mapping
    adapters/           LLM tools storage and workflow implementations
    bootstrap/          Dependency providers and application factory
    workers/            Background entry points calling usecases
  tests/unit/usecases/
  tests/unit/controllers/
  tests/integration/
frontend/
  src/lib/components/
  src/lib/features/
  src/lib/api/
  src/routes/
  tests/unit/components/
  tests/unit/routes/
  tests/unit/api/
  tests/mocks/
  tests/coverage-map.json
deploy/
```

Organize files within each layer by feature, including authentication, engagements, runs, findings, retests, scoring, system prompts, reports, and audit. Avoid a single large usecase or controller containing unrelated application behavior. Exclude generated files, dependencies, and test-only harnesses from the shipped-source inventory, but do not exclude application components simply because they are small.

## 3 Backend layer architecture

The requested foundation-to-entrypoint structure is:

```text
Database -> Repository -> Usecase -> Controller
```

An incoming request executes in the opposite direction through those layers:

```text
HTTP request -> Controller -> Usecase -> Repository -> Database
HTTP response <- Controller <- Usecase <- Repository <- Database
```

Source dependencies use inversion at the application boundary: usecases reference repository and service interfaces declared in ports, and concrete repositories implement those interfaces. The composition root assembles the implementations. The arrows above describe the stack and runtime flow; they do not authorize a controller to skip a layer.

| Layer | Responsibilities | Boundary rules |
| --- | --- | --- |
| Database | Schema, migrations, constraints, indexes, session and connection infrastructure. | No HTTP handling or application workflow decisions. |
| Repository | Query and persist records, translate persistence objects, implement scoped access and versioned writes. | No HTTP responses, tool execution, LLM reasoning, or independent business transaction commits. |
| Usecase | Enforce authorization, scope, state transitions, business invariants, transaction boundaries, audit intent, and external-work scheduling. | No SQL, ORM sessions, framework request objects, or concrete provider clients. |
| Controller | Parse and validate transport input, resolve the authenticated actor, invoke a usecase, and map output or errors to HTTP. | No direct repository or database calls and no business decision logic. |

Domain entities and errors must remain usable without FastAPI or a running database. Usecases accept typed application inputs and return application results. HTTP request and response models belong at the controller boundary. ORM objects must not leak into frontend responses or application policies.

Repository operations must support project or engagement constraints and expected-version checks. A usecase must not authorize access by trusting an object identifier or role supplied in a request body. Workers invoke the same application usecases through injected ports; they do not bypass policies by writing directly to tables.

## 4 Dependency injection and transaction ownership

Use constructor injection for usecases. Inject repository interfaces, a unit-of-work interface, authorization services where needed, audit capture, a clock, identifier generation, the model gateway, tool execution, workflow scheduling, and evidence storage. Inject only collaborators required by that usecase.

```text
Composition root
  -> request scoped unit of work and repository implementations
  -> service adapters and clock
  -> usecase instance
  -> controller dependency
```

Resolve HTTP dependencies through framework providers at the composition boundary. FastAPI dependency overrides can replace providers in controller-boundary tests. Usecases themselves must not import Depends, HTTPException, framework request objects, or a global service locator. A controller must not construct its repository or provider client inline. Keep provider overrides isolated to each test and restore them during teardown.

Database sessions and transactions have explicit lifetimes. A background task opens its own unit of work; it must never retain a request-scoped session after the request ends. Long-running scans and model calls do not hold open database transactions.

The usecase owns the logical transaction. Persist a state mutation and its required audit event together, with an outbox entry when work must be dispatched after commit. Repositories do not commit independently. Publish external work only after durable intent exists, and use idempotency keys or reconciliation for retries. A failed commit cannot leave a supposedly accepted action with no durable record. Failure and denial audit paths must also follow the FRD policy.

Enforce layer boundaries with an automated import or architecture check. In particular, fail checks for controller imports of concrete repositories or db modules, usecase imports of db or controllers, and usecase imports of concrete model or tool adapters. Domain and ports must not import concrete outer-layer modules. Composition and worker entrypoints are the permitted assembly boundaries.

## 5 Backend unit testing standard

Use pytest with the appropriate pinned async test support where the implementation is asynchronous. Unit tests run without a real database, model endpoint, target application, scanner process, queue, or evidence store. Construct usecases directly with interface-conforming fakes or mocks. Use deterministic clocks and IDs. Reset fakes, environment changes, and overrides between tests.

### 5.1 Usecase tests

Every application action must have a test mapping and behavior assertions. Cover success, invalid input or state, denied access, missing resources, expected-version conflicts, idempotent replay, collaborator failure, and cancellation where relevant. Check returned state and persisted intent, not only mock call counts.

Tests must also assert the absence of prohibited effects: a denied action must not modify a finding, dispatch a scan, activate a system prompt, or call an LLM. For transactional behavior, use a fake unit of work that exposes commit and rollback outcomes. Verify atomic audit and scheduling intent under failure. Real transaction and database-constraint guarantees require separate repository integration tests.

### 5.2 Controller tests

Test controller behavior with a stubbed usecase and authenticated-actor provider. Verify request-to-command mapping, response shape, status, cookie behavior where applicable, and domain-error translation. Do not connect real repositories to controller unit tests.

Pure controller tests can invoke extracted transport mapping functions directly. Add in-process HTTP boundary tests against the relevant router and application middleware with dependencies overridden to stubs. These boundary tests verify validation, authentication challenges, CSRF enforcement, and exception mapping; they supplement the isolated unit suite and must not be described as full database integration tests.

| Condition | Expected controller behavior |
| --- | --- |
| Missing or invalid session | Reject protected access with the documented unauthenticated response. |
| Valid session but insufficient permission | Return the documented forbidden or access-masking response without exposing restricted content. |
| Invalid request shape | Return validation details that do not contain secrets. |
| Missing permitted resource | Return the documented not-found response. |
| Stale version or invalid run transition | Return a conflict that the frontend can present and reconcile. |
| Accepted asynchronous action | Return an accepted action identifier and actual current state, not a false completed state. |
| Unexpected dependency failure | Return a sanitized error and correlation identifier; preserve diagnostic detail only in protected logs. |

Use the API contract consistently for exact status codes. A hidden frontend button is never a substitute for controller and usecase authorization tests.

## 6 Product specific backend test cases

| Feature | Required examples | Requirement links |
| --- | --- | --- |
| Authentication | Password alone cannot create a full session; invalid or replayed TOTP fails; logout revokes the session. | FR-AUTH-002 to FR-AUTH-006 |
| Run controls | Repeated commands are idempotent; stop wins over resume; unacknowledged workers prevent a false stopped state. | FR-RUN-001 to FR-RUN-006 |
| Findings and scoring | Evidence is required; manual overrides survive regeneration; CVSS inputs use deterministic calculation. | FR-FIND-001 to FR-FIND-004 and FR-SCORE |
| Retesting | Only selected findings and approved prerequisites run; interrupted or inaccessible checks cannot mark fixed; prior evidence remains unchanged. | FR-FIND-005 to FR-FIND-007 |
| System prompts | Only Administrators manage system instructions; published versions are immutable; activation does not alter pinned runs. | FR-PROMPT-001 to FR-PROMPT-005 |
| Model gateway | Profile and data-boundary checks apply; malformed output cannot schedule tools; no automatic cloud fallback. | FR-LLM-001 to FR-LLM-004 |
| Audit | Actor chain and affected assets are recorded; required audit failure blocks the protected operation. | FR-AUDIT-001 to FR-AUDIT-004 |
| Reporting | Only approved snapshots issue final PDFs; partial runs remain partial; overrides and retest outcomes match the snapshot. | FR-REPORT-001 to FR-REPORT-004 |

Use injected fakes for side effects while exercising the actual application policies. Keep calculator reference tests, real database transaction tests, worker termination tests, and report-rendering checks in their appropriate additional suites; passing unit tests alone does not verify those operational properties.

## 7 SvelteKit SPA implementation

Use SvelteKit with TypeScript and client-side rendering for the application. Set the root layout page option to disable SSR, use adapter-static with an SPA fallback, and configure the on-premises web server to serve that fallback for frontend routes. Select exact configuration syntax for the pinned SvelteKit major version from its documentation; configuration locations can change between major versions.

The page option is:

```typescript
// frontend/src/routes/+layout.ts
export const ssr = false;
```

Keep application APIs in the separate backend. Do not implement platform business logic in SvelteKit server routes, server loads, remote functions requiring a server runtime, or server form actions. Submit browser forms through the backend HTTP API. Universal client load functions may load data through the shared API client and must be tested.

Serve static frontend assets and the backend under one on-premises origin where practical. For example, route /api/ to the backend and route application paths to the SPA shell. API failures and missing asset requests must not be rewritten into a successful HTML fallback. Verify refresh and direct entry on nested routes, with configured base paths preserved.

The backend owns sessions, password and TOTP verification, authorization, and CSRF validation. The frontend loads the current session from a backend endpoint and uses HTTP-only cookies. It may control visible actions for usability, but every protected operation is checked again by the backend. Do not put session credentials, provider keys, or system prompt bodies in local storage, public environment variables, or static build output.

## 8 Frontend boundaries and page behavior

Use a shared typed HTTP client in src/lib/api for base URLs, credentials, CSRF headers, error normalization, abort signals, and response decoding. Feature modules expose application-specific requests to pages and components. Prevent ad hoc fetch calls scattered across visual components.

Pages assemble feature views and route state. Components use typed props and explicit events or callbacks. Shared state has a documented owner and reset behavior, especially on logout or project changes. Browser timers, navigation, downloads, and live-update transports are wrapped or injected where needed for deterministic tests.

Build pages for authentication and TOTP, engagement setup, live run control, coverage, findings and severity editing, finding retests, report review and downloads, audit exploration, and administration. The Administrator system prompt screen selects an agent and LLM profile and manages only system instructions. User task inputs remain separate. Require the existing role and access behavior on each surface.

Run controls must show PAUSING and STOPPING until backend state confirms completion. Handle stale updates, reconnects, and disabled controls. A retest view shows outcomes per selected finding and previous validated disposition. Severity editing distinguishes calculated CVSS, manual reported severity, and business risk.

## 9 Unit tests for every component and page

Use Vitest with Svelte Testing Library, user-event utilities, and a pinned DOM environment such as jsdom. Configure Svelte's browser resolution and cleanup using the integration appropriate to the selected versions. For components that depend on real browser behavior, add an appropriate component browser test; do not assume a simulated DOM verifies layout or cookie security.

Every shipped .svelte component and route page must have meaningful unit tests. Include layouts, error views, feature components, dialogs, forms, and loading views. A presentational component needs render and relevant prop or accessibility assertions. An interactive component needs interaction and state assertions. Pages must test their actual page component or its route harness, rather than only a mocked child that replaces the behavior under test.

| Surface | Minimum behavioral assertions when applicable |
| --- | --- |
| Presentational component | Visible content, relevant prop variants, semantic role, and accessible name. |
| Form or dialog | Validation, submit payload, pending state, success, cancellation, and failure feedback. |
| Data page | Loading, populated, empty, forbidden or unauthenticated, and error states. |
| Run control page | Pause or stop request, intermediate state, confirmed state, stale response, and failed request. |
| Finding and retest page | Selected IDs, individual results, original evidence visibility, preserved override, and inconclusive outcome. |
| System prompt administration | Administrator access, non-Administrator denial, draft changes, validation failure, version comparison, activation, and rollback. |
| Layout or error view | Session transition, navigation, nested content, route error, and logout cleanup. |

Mock SvelteKit navigation and route state at the framework boundary when necessary. Test client load functions, API helpers, stores, and state utilities as well as the Svelte files that use them. Assert behavior through accessible queries and user interactions. Snapshots may supplement assertions but cannot be the sole test of an interactive page.

Maintain frontend/tests/coverage-map.json mapping every shipped source component and page to its test files. A CI inventory check must compare this map with the discovered source files and verify that mapped tests contain the corresponding render or behavior tests and are actually collected. New or renamed components fail this check until their tests are included. A checked-in map alone does not demonstrate coverage.

Keep route tests in tests/unit/routes, using names such as findings.page.test.ts and prompts.page.test.ts. Avoid creating unrecognized reserved plus-prefixed route files for test naming. The test inventory requirement is 100 percent of shipped components and pages; it is distinct from statement or branch coverage.

## 10 Mocking every frontend HTTP call

Use Mock Service Worker for unit-test HTTP interception so components exercise the real API client against controlled responses. All application HTTP requests must have explicit handlers. Configure unhandled requests as test failures, and enforce rejection or deny unexpected real network access in the test harness. A warning alone does not satisfy this rule.

Start the interceptor before tests, reset per-test handlers after each test, and close it after the suite. Clear application state, restore mocks and timers, and clean up mounted components. Validate request method, path, query, relevant headers, and body for mutations. Do not use a permissive catch-all handler that silently makes unknown calls succeed.

Cover successful responses, validation errors, unauthenticated and forbidden responses, stale-version conflicts, rate limits where supported, server errors, network failures, cancellation, and malformed responses. Explicitly control delayed responses rather than sleeping. Use fake timers for polling and settle scheduled work before teardown. Mock live-update transports as well if the page uses them.

The test process must not contact the real backend, real target, model provider, or production storage. Use synthetic fixtures with no actual secrets or personal information. HTTP-only cookie behavior, actual CSRF enforcement, and browser session security need backend and browser-level checks in addition to frontend mocks; a mocked successful login does not verify them.

## 11 Unit test inventory and coverage gates

Every usecase and controller must be mapped to collected tests, and every frontend component and page must be mapped to collected tests. Required business and failure branches must have assertions even if aggregate coverage passes. Include unimported application source in coverage collection so an untested file cannot disappear from the denominator.

Proposed numerical coverage floors for review are 90 percent statements and 85 percent branches across backend usecases and controllers, and 85 percent statements and 80 percent branches across frontend application code. Enforce the selected floors in CI, including the required layer or feature scope rather than only a repository-wide average. These proposed floors do not replace the mandatory per-file inventory or successful execution of every required test.

Required tests cannot be skipped, marked expected-failure, left as todo, or removed to produce a passing result. Fail on zero collected tests, unhandled async errors, unexpected HTTP, stale snapshots, and missing inventory entries. Do not use retries to conceal failures; fix the cause and rerun the affected suite, then the complete required unit suites.

## 12 Commands and continuous integration

During repository setup, implement and document scripts for architecture checks, backend test inventory, frontend test inventory, linting, type checking, unit execution, coverage checks, and builds. The following commands are the intended contract once dependencies and scripts are installed and pinned; they are not evidence of a completed run.

From the backend working directory, inside the project's managed Python environment:

```text
python scripts/check_architecture.py
python scripts/check_test_inventory.py
python -m pytest tests/unit/usecases tests/unit/controllers \
  --junitxml=artifacts/backend-unit.xml \
  --cov=pentest_platform.usecases \
  --cov=pentest_platform.controllers \
  --cov-branch --cov-report=xml:artifacts/backend-coverage.xml \
  --cov-report=term-missing
```

Use the pinned coverage tooling and a policy check to enforce both statement and branch floors; a single combined coverage percentage is insufficient. Ensure the application package is installed in the test environment and the artifacts directory exists.

From the frontend working directory:

```text
pnpm install --frozen-lockfile
pnpm run lint
pnpm run check
pnpm run test:inventory
pnpm run test:unit
pnpm run build
```

Define test:unit as a non-watch Vitest run with coverage and machine-readable results. Configure separate output files for JUnit and coverage reports. test:inventory is a repository-owned script implementing the component and page inventory rule; it is not a built-in SvelteKit command. Pin package-manager and runtime versions and validate configuration against the lockfile.

CI jobs must fail if either backend or frontend unit tests fail. Tests run in a controlled environment with no real target or provider credentials and no dependency on a live application backend. Execute both required unit suites against the final source revision before merge or release, including for changes that affect only one side of the application.

## 13 Development workflow and completion criteria

For each change, identify affected FR and NFR IDs; define inputs, errors, and side effects; implement repository contracts and usecases; wire controllers through dependency injection; implement frontend behavior; and add tests alongside the change. Run focused tests while editing, then execute all required unit suites and the inventory and architecture checks on the final source revision. Fix failures before declaring the change complete.

Backend completion requires correct layer boundaries, dependency injection, tested application policies, tested controller mapping, and passing usecase and controller suites. Frontend completion requires SvelteKit SPA behavior, tests for every shipped component and page, mocked HTTP, and a passing full frontend unit suite. Both require lint and type checks, a successful build where applicable, and no missing test inventory entries.

Record commit or source revision, lockfile versions, exact commands, execution time, collected and passed counts, failures, skips, coverage, and report locations. The mandatory unit result is all collected required tests passed, zero failures, and no skipped required tests. If tests cannot run, state the blocker and do not label the implementation verified or ready to merge.

Integration and browser acceptance checks remain necessary for database constraints and migrations, actual session cookies, SPA deep links, worker cancellation, model compatibility, real scope enforcement, PDF rendering, and backup recovery. Keep these checks additional to the requested unit suites.

## 14 Official implementation references

Use these primary references for the selected package versions. The layer rules, test inventory, and passing-test gates are project requirements; library documentation supplies integration details. Pin versions and review upgrade changes before modifying configuration.

- SvelteKit SPA configuration: https://svelte.dev/docs/kit/single-page-apps
- Svelte testing guidance: https://svelte.dev/docs/svelte/testing
- Svelte Testing Library setup: https://testing-library.com/docs/svelte-testing-library/setup/
- Vitest request mocking: https://vitest.dev/guide/mocking/requests
- FastAPI dependency overrides: https://fastapi.tiangolo.com/advanced/testing-dependencies/
- pytest mocking and fixtures: https://docs.pytest.org/en/stable/how-to/monkeypatch.html
