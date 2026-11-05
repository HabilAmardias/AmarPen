from pentest_platform.domain.entities import CoverageRecord, Scenario
from pentest_platform.usecases.testing import TestingUsecase
from tests.fakes import actor


def test_list_scenarios_only_returns_enabled(base_kwargs, repo, ids):
    repo.repo.add(Scenario(id=ids.new_id(), key="A", version="1", title="A", enabled=True))
    repo.repo.add(Scenario(id=ids.new_id(), key="B", version="1", title="B", enabled=False))
    scenarios = TestingUsecase(**base_kwargs).list_scenarios(actor())
    assert [scenario.key for scenario in scenarios] == ["A"]


def test_coverage_groups_counts(base_kwargs, repo, ids, engagement):
    scenario = Scenario(id=ids.new_id(), key="A", version="1", title="A")
    repo.repo.add(scenario)
    repo.repo.add(
        CoverageRecord(
            id=ids.new_id(),
            run_id="run-1",
            engagement_id=engagement.id,
            scenario_id=scenario.id,
            target="example.com",
            status="TESTED_NO_ISSUE_OBSERVED",
        )
    )
    result = TestingUsecase(**base_kwargs).coverage(actor(), engagement.id)
    assert result["counts"]["TESTED_NO_ISSUE_OBSERVED"] == 1
    assert result["records"][0]["scenario"] == "A"
