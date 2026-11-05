import dataclasses
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from pentest_platform.domain.entities import AuditEvent, User
from pentest_platform.domain.enums import AuditOutcome
from pentest_platform.domain.principal import Actor, SystemActor


class InMemoryRepository:
    def __init__(self):
        self.store: dict[str, list[Any]] = {}

    def add(self, entity: Any) -> Any:
        self.store.setdefault(type(entity).__name__, []).append(entity)
        return entity

    def update(self, entity: Any) -> Any:
        items = self.store.setdefault(type(entity).__name__, [])
        for index, item in enumerate(items):
            if item.id == entity.id:
                items[index] = entity
                return entity
        items.append(entity)
        return entity

    def delete(self, entity: Any) -> None:
        items = self.store.setdefault(type(entity).__name__, [])
        self.store[type(entity).__name__] = [item for item in items if item.id != entity.id]

    def get(self, entity_type, entity_id: str):
        for item in self.store.get(entity_type.__name__, []):
            if item.id == entity_id:
                return item
        return None

    def find_one(self, entity_type, **filters):
        items = self.list(entity_type, **filters)
        return items[0] if items else None

    def list(self, entity_type, **filters):
        items = self.store.get(entity_type.__name__, [])
        return [
            item
            for item in items
            if all(getattr(item, key) == value for key, value in filters.items())
        ]

    def count(self, entity_type, **filters):
        return len(self.list(entity_type, **filters))

    def claim_tasks(self, worker_id, now, lease_seconds, limit):

        runs = {item.id: item for item in self.store.get("Run", [])}
        claimed = []
        for task in self.store.get("Task", []):
            if len(claimed) >= limit:
                break
            if task.state != "QUEUED":
                continue
            if task.next_attempt_at is not None and task.next_attempt_at > now:
                continue
            run = runs.get(task.run_id)
            if run is None or run.state != "RUNNING":
                continue
            task.state = "RUNNING"
            task.worker_id = worker_id
            task.lease_id = secrets.token_hex(8)
            task.authority_expires_at = now + timedelta(seconds=lease_seconds)
            task.attempt += 1
            task.next_attempt_at = None
            task.updated_at = now
            claimed.append(task)
        return claimed

    def requeue_expired_tasks(self, now, retry_delay_seconds=15):
        recovered = []
        for task in self.store.get("Task", []):
            if task.state == "RUNNING" and task.authority_expires_at and task.authority_expires_at < now:
                if task.attempt >= task.max_attempts:
                    task.state = "FAILED"
                else:
                    task.state = "QUEUED"
                    task.next_attempt_at = now + timedelta(seconds=retry_delay_seconds)
                task.outcome = "LEASE_EXPIRED"
                task.worker_id = ""
                task.lease_id = ""
                task.authority_expires_at = None
                recovered.append(task)
        return recovered

    def ensure_budget(self, ledger):
        from pentest_platform.domain.entities import BudgetLedger

        existing = self.find_one(BudgetLedger, run_id=ledger.run_id)
        if existing is None:
            self.add(ledger)
            return ledger
        return existing

    def consume_budget(self, run_id, now, *, requests=0, model_calls=0, iterations=0, tasks=0):
        from pentest_platform.domain.entities import BudgetLedger

        ledger = self.find_one(BudgetLedger, run_id=run_id)
        if ledger is None:
            return False
        if (
            ledger.request_used + requests > ledger.request_limit
            or ledger.model_used + model_calls > ledger.model_limit
            or ledger.iteration_used + iterations > ledger.iteration_limit
            or ledger.task_used + tasks > ledger.task_limit
        ):
            return False
        ledger.request_used += requests
        ledger.model_used += model_calls
        ledger.iteration_used += iterations
        ledger.task_used += tasks
        ledger.version += 1
        ledger.updated_at = now
        return True

    def acquire_lock(self, run_id, lock_key, owner_task_id, now, expires_at):
        from pentest_platform.domain.entities import ResourceLock

        self.release_expired_locks(now)
        if any(
            lock.run_id == run_id and lock.lock_key == lock_key and lock.state == "HELD" and lock.expires_at > now
            for lock in self.store.get("ResourceLock", [])
        ):
            return False
        self.add(
            ResourceLock(
                id=secrets.token_hex(8),
                run_id=run_id,
                lock_key=lock_key,
                owner_task_id=owner_task_id,
                acquired_at=now,
                expires_at=expires_at,
            )
        )
        return True

    def release_lock(self, owner_task_id, now):
        for lock in self.store.get("ResourceLock", []):
            if lock.owner_task_id == owner_task_id and lock.state == "HELD":
                lock.state = "RELEASED"
                lock.released_at = now

    def release_expired_locks(self, now):
        for lock in self.store.get("ResourceLock", []):
            if lock.state == "HELD" and lock.expires_at <= now:
                lock.state = "EXPIRED"
                lock.released_at = now


class FakeUnitOfWork:
    def __init__(self, repo=None):
        self.repo = repo or InMemoryRepository()
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.rollbacks += 1


class FakeAudit:
    def __init__(self, clock):
        self.clock = clock
        self.events: list[AuditEvent] = []

    def record(self, repo, *, actor, action, resource, outcome=AuditOutcome.SUCCESS, **kwargs):
        if isinstance(actor, Actor):
            actor_type, actor_id = "user", actor.user_id
        elif isinstance(actor, SystemActor):
            actor_type, actor_id = actor.actor_type, actor.actor_id
        else:
            actor_type, actor_id = "unauthenticated", "anonymous"
        event = AuditEvent(
            id=f"audit-{len(self.events)}",
            event_id=f"event-{len(self.events)}",
            occurred_at=self.clock.now(),
            recorded_at=self.clock.now(),
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource=resource,
            outcome=str(outcome),
            details=kwargs.get("details", {}),
        )
        self.events.append(event)
        repo.add(event)
        return event


class FixedClock:
    def __init__(self, now: datetime | None = None):
        self._now = now or datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs) -> None:
        from datetime import timedelta

        self._now = self._now + timedelta(**kwargs)


class SequentialIds:
    def __init__(self):
        self.index = 0

    def new_id(self) -> str:
        self.index += 1
        return f"id-{self.index}"

    def new_token(self, length: int = 32) -> str:
        self.index += 1
        return f"token-{self.index}"


class FakePasswordService:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == f"hashed:{password}"

    def validate_strength(self, password: str) -> None:
        if len(password) < 12:
            from pentest_platform.domain.errors import ValidationError

            raise ValidationError("Password must be at least 12 characters")


class FakeTotpService:
    def __init__(self):
        self.step = 100

    def generate_secret(self) -> str:
        return "JBSWY3DPEHPK3PXP"

    def provisioning_uri(self, secret: str, username: str) -> str:
        return f"otpauth://totp/{username}?secret={secret}"

    def verify(self, secret: str, code: str, last_step: int | None = None) -> int | None:
        if code != "123456":
            return None
        if last_step is not None and last_step >= self.step:
            return None
        return self.step

    def encrypt(self, secret: str) -> str:
        return f"enc:{secret}"

    def decrypt(self, encrypted: str) -> str:
        return encrypted.removeprefix("enc:")


class FakeEvidenceStore:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.objects[key] = data
        return key

    def get(self, key: str) -> bytes:
        return self.objects[key]

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    def health(self) -> bool:
        return True


class FakeReportRenderer:
    def render(self, report: dict) -> bytes:
        return b"%PDF-1.4 fake\n" + str(report.get("title", "")).encode()


class FakeToolRunner:
    def __init__(self, findings=None):
        self.findings = findings or []
        self.calls: list[tuple[str, dict]] = []

    def available(self, tool: str) -> bool:
        return True

    def run(self, tool: str, parameters: dict, *, timeout: int = 60) -> dict:
        self.calls.append((tool, parameters))
        return {"outcome": "COMPLETED", "findings": self.findings, "target": parameters.get("target")}


class FakeLlmGateway:
    def __init__(self, responses: dict | None = None, fail: bool = False, invalid: bool = False):
        self.responses = responses or {}
        self.fail = fail
        self.invalid = invalid
        self.calls: list[dict] = []

    def complete(self, profile, messages, schema=None):
        from pentest_platform.domain.errors import DependencyUnavailableError

        if self.fail:
            raise DependencyUnavailableError("model unavailable")
        context = {}
        for message in messages:
            content = message.get("content", "")
            if content.startswith("AGENT_CONTEXT:\n"):
                import json

                context = json.loads(content.removeprefix("AGENT_CONTEXT:\n"))
        role = context.get("agent_role", "orchestrator")
        self.calls.append({"role": role, "context": context})
        if self.invalid:
            return {"content": {"unexpected": True}}
        payload = self.responses.get(role) or self._default(role, context)
        return {"content": payload}

    @staticmethod
    def _default(role, context):
        targets = context.get("targets", ["example.com"])
        target = targets[0] if targets else "example.com"
        if role == "orchestrator":
            return {
                "tasks": [
                    {
                        "role": "discovery",
                        "kind": "discovery",
                        "scenario_key": "WSTG-INFO-01",
                        "asset": target,
                        "reason": "Map the approved target",
                        "depends_on": [],
                    }
                ]
            }
        if role == "discovery":
            return {"assets": [{"kind": "target", "value": target}]}
        if role in {"web_testing", "api_testing", "authorization_business_logic"}:
            return {"candidates": [], "coverage_status": "TESTED_NO_ISSUE_OBSERVED"}
        if role == "validation":
            return {"verdict": "VALIDATED", "rationale": "Evidence supports the candidate"}
        if role == "risk_assessment":
            return {
                "cvss_vector": "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:N",
                "cvss_rationale": {"AV": "network"},
                "business_likelihood": 4,
                "business_impact": 4,
                "business_rationale": "Material business impact",
                "confidence": "high",
            }
        if role == "reporting":
            return {
                "executive_summary": "Agent draft summary",
                "scope": "Authorized external targets",
                "methodology": "Catalogue-driven assessment",
                "limitations": [],
            }
        return {}

    def health(self, profile):
        return not self.fail


class FakeContainer:
    def __init__(self, settings):
        self.settings = settings
        self.evidence_store = FakeEvidenceStore()

    def audit_healthy(self) -> bool:
        return True


def actor(roles=("Administrator", "Analyst"), user_id="user-1", username="admin") -> Actor:
    return Actor(user_id=user_id, username=username, roles=frozenset(roles))


def user(
    user_id="user-1",
    username="admin",
    roles=("Administrator", "Analyst"),
    totp_enabled=True,
    password_hash="hashed:correct horse battery",
) -> User:
    return User(
        id=user_id,
        username=username,
        password_hash=password_hash,
        totp_secret_enc="enc:JBSWY3DPEHPK3PXP",
        totp_enabled=totp_enabled,
        roles=list(roles),
        bootstrapped=True,
    )


def entity_dict(entity) -> dict:
    return dataclasses.asdict(entity)
