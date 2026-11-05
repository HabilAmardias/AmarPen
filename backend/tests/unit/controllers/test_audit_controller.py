from pentest_platform.controllers.deps import get_actor, get_audit
from pentest_platform.domain.entities import AuditEvent
from pentest_platform.usecases.common import utc_now
from tests.fakes import actor
from tests.unit.controllers.helpers import make_client

EVENT = AuditEvent(
    id="audit-1",
    event_id="event-1",
    occurred_at=utc_now(),
    recorded_at=utc_now(),
    actor_type="user",
    actor_id="user-1",
    action="engagement.created",
    resource="engagement:1",
    outcome="SUCCESS",
)


class StubAudit:
    def search(self, actor, filters, page, page_size):
        return [EVENT], {"page": page, "page_size": page_size, "total": 1, "pages": 1}

    def export(self, actor, filters, export_format):
        return b'[{"event_id": "event-1"}]', "application/json"


def test_search_and_export_audit():
    client = make_client({get_actor: lambda: actor(), get_audit: lambda: StubAudit()})
    response = client.get("/api/v1/audit/events")
    assert response.status_code == 200
    assert response.json()["items"][0]["event_id"] == "event-1"
    exported = client.get("/api/v1/audit/export")
    assert exported.status_code == 200
    assert b"event-1" in exported.content
