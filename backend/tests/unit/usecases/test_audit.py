import json

from pentest_platform.domain.entities import AuditEvent
from pentest_platform.usecases.audit import AuditUsecase
from tests.fakes import actor


def add_event(repo, clock, ids, action="engagement.created"):
    event = AuditEvent(
        id=ids.new_id(),
        event_id=ids.new_id(),
        occurred_at=clock.now(),
        recorded_at=clock.now(),
        actor_type="user",
        actor_id="user-1",
        action=action,
        resource="engagement:1",
        outcome="SUCCESS",
    )
    repo.repo.add(event)
    return event


def test_search_filters_and_paginates(base_kwargs, repo, clock, ids):
    add_event(repo, clock, ids, "engagement.created")
    add_event(repo, clock, ids, "finding.validated")
    usecase = AuditUsecase(**base_kwargs)
    events, meta = usecase.search(actor(), {"action": "finding.validated"}, page=1, page_size=10)
    assert len(events) == 1
    assert meta["total"] == 1


def test_export_json_and_csv(base_kwargs, repo, clock, ids):
    add_event(repo, clock, ids)
    usecase = AuditUsecase(**base_kwargs)
    content, media_type = usecase.export(actor(), {}, "json")
    assert media_type == "application/json"
    assert json.loads(content)[0]["action"] == "engagement.created"
    csv_content, csv_type = usecase.export(actor(), {}, "csv")
    assert csv_type == "text/csv"
    assert b"event_id" in csv_content
