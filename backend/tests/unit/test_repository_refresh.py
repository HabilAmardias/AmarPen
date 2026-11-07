from pentest_platform.db.models import RunRow
from pentest_platform.db.session import create_schema, create_session_factory
from pentest_platform.domain.entities import Run
from pentest_platform.repositories.sqlalchemy_repository import SqlAlchemyRepository


def test_run_controls_refresh_even_when_session_retains_cached_row(tmp_path):
    engine, factory = create_session_factory(f"sqlite:///{tmp_path / 'controls.db'}")
    create_schema(engine)
    with factory() as first, factory() as second:
        repository = SqlAlchemyRepository(first)
        repository.add(Run(id="run", engagement_id="engagement", state="RUNNING"))
        first.commit()
        cached = first.get(RunRow, "run")
        assert cached.state == "RUNNING"
        other = second.get(RunRow, "run")
        other.state = "STOPPING"
        second.commit()
        assert repository.get(Run, "run").state == "STOPPING"
    engine.dispose()
