"""Tests for the aggregators module."""

import pytest
import time
from outcome_tracker import (
    OutcomeTracker,
    RewardDomain,
    OutcomeType,
)
from outcome_tracker.aggregators import (
    TimeWindowAggregator,
    DomainAggregator,
    CharacterAggregator,
    CustomAggregator,
    TimeWindow,
    AggregationResult,
)


class TestTimeWindow:
    """Tests for TimeWindow class."""

    def test_contains(self):
        window = TimeWindow(start=1000.0, end=2000.0)
        assert window.contains(1500.0) is True
        assert window.contains(1000.0) is True
        assert window.contains(2000.0) is True
        assert window.contains(999.0) is False
        assert window.contains(2001.0) is False

    def test_contains_with_label(self):
        window = TimeWindow(start=0.0, end=100.0, label="test_window")
        assert window.label == "test_window"
        assert window.contains(50.0) is True

    def test_empty_window(self):
        window = TimeWindow(start=100.0, end=100.0)
        assert window.contains(100.0) is True
        assert window.contains(99.9) is False


class TestAggregationResult:
    """Tests for AggregationResult class."""

    def test_success_rate(self):
        result = AggregationResult(
            key="test", count=10, success_count=7,
            total_reward=3.5, avg_reward=0.35,
        )
        assert result.success_rate == 0.7

    def test_success_rate_zero_count(self):
        result = AggregationResult(
            key="test", count=0, success_count=0,
            total_reward=0.0, avg_reward=0.0,
        )
        assert result.success_rate == 0.0

    def test_success_rate_all_success(self):
        result = AggregationResult(
            key="test", count=5, success_count=5,
            total_reward=2.5, avg_reward=0.5,
        )
        assert result.success_rate == 1.0

    def test_success_rate_all_failure(self):
        result = AggregationResult(
            key="test", count=5, success_count=0,
            total_reward=0.0, avg_reward=0.0,
        )
        assert result.success_rate == 0.0

    def test_to_dict(self):
        result = AggregationResult(
            key="test", count=5, success_count=3,
            total_reward=1.5, avg_reward=0.3,
            domain_breakdown={"combat": 0.5},
        )
        data = result.to_dict()
        assert data["key"] == "test"
        assert data["count"] == 5
        assert data["success_rate"] == 0.6
        assert data["avg_reward"] == 0.3
        assert data["domain_breakdown"] == {"combat": 0.5}

    def test_to_dict_with_metadata(self):
        result = AggregationResult(
            key="test", count=3, success_count=2,
            total_reward=1.0, avg_reward=0.33,
            metadata={"window_start": 100.0, "window_end": 200.0},
        )
        data = result.to_dict()
        assert data["metadata"]["window_start"] == 100.0


class TestTimeWindowAggregator:
    """Tests for TimeWindowAggregator class."""

    @pytest.fixture
    def tracker(self):
        tracker = OutcomeTracker()
        now = time.time()
        tracker.track_immediate_outcome(
            decision_id="early", description="Early outcome", success=True,
            context={"decision_type": "combat_action"},
        )
        tracker.outcomes["early"][0].timestamp = now - 7200  # 2 hours ago
        tracker.track_immediate_outcome(
            decision_id="recent", description="Recent outcome", success=True,
            context={"decision_type": "social"},
        )
        tracker.outcomes["recent"][0].timestamp = now - 300  # 5 minutes ago
        return tracker

    def test_aggregate_by_window(self, tracker):
        aggregator = TimeWindowAggregator(tracker)
        now = time.time()
        windows = [
            TimeWindow(now - 3600, now, "last_hour"),
            TimeWindow(now - 7200, now - 3600, "previous_hour"),
        ]
        results = aggregator.aggregate_by_window(windows)
        assert len(results) == 2
        assert results[0].key == "last_hour"
        assert results[1].key == "previous_hour"

    def test_aggregate_last_n_minutes(self, tracker):
        aggregator = TimeWindowAggregator(tracker)
        result = aggregator.aggregate_last_n_minutes(10)
        assert result.key == "last_10_min"
        assert result.count == 1

    def test_aggregate_empty_tracker(self):
        tracker = OutcomeTracker()
        aggregator = TimeWindowAggregator(tracker)
        result = aggregator.aggregate_last_n_minutes(60)
        assert result.count == 0

    def test_aggregate_by_window_empty(self):
        tracker = OutcomeTracker()
        aggregator = TimeWindowAggregator(tracker)
        now = time.time()
        results = aggregator.aggregate_by_window([
            TimeWindow(now - 3600, now, "test")
        ])
        assert results[0].count == 0

    def test_aggregate_last_n_minutes_large_window(self, tracker):
        aggregator = TimeWindowAggregator(tracker)
        result = aggregator.aggregate_last_n_minutes(10000)  # ~7 days
        assert result.count == 2

    def test_aggregate_by_interval(self, tracker):
        aggregator = TimeWindowAggregator(tracker)
        results = aggregator.aggregate_by_interval(3600)
        assert len(results) >= 1
        for r in results:
            assert r.count >= 0


class TestDomainAggregator:
    """Tests for DomainAggregator class."""

    @pytest.fixture
    def tracker(self):
        tracker = OutcomeTracker()
        tracker.track_immediate_outcome(
            decision_id="combat_1", description="Hit for 15 damage", success=True,
            context={"decision_type": "combat_action"},
        )
        tracker.track_immediate_outcome(
            decision_id="combat_2", description="Took 5 damage but kept fighting", success=False,
            context={"decision_type": "combat_action"},
        )
        tracker.track_immediate_outcome(
            decision_id="social_1", description="Convinced merchant", success=True,
            context={"decision_type": "social"},
        )
        return tracker

    def test_aggregate_by_domain(self, tracker):
        aggregator = DomainAggregator(tracker)
        results = aggregator.aggregate_by_domain()
        assert RewardDomain.COMBAT in results
        assert RewardDomain.SOCIAL in results
        combat = results[RewardDomain.COMBAT]
        assert combat.count == 2

    def test_get_domain_summary(self, tracker):
        aggregator = DomainAggregator(tracker)
        summary = aggregator.get_domain_summary()
        assert "combat" in summary
        assert "social" in summary
        assert summary["combat"]["count"] == 2

    def test_get_best_domain(self, tracker):
        aggregator = DomainAggregator(tracker)
        best = aggregator.get_best_domain()
        assert best is not None
        assert isinstance(best, RewardDomain)

    def test_get_worst_domain(self, tracker):
        aggregator = DomainAggregator(tracker)
        worst = aggregator.get_worst_domain()
        assert worst is not None
        assert isinstance(worst, RewardDomain)

    def test_empty_tracker(self):
        tracker = OutcomeTracker()
        aggregator = DomainAggregator(tracker)
        results = aggregator.aggregate_by_domain()
        assert len(results) == 0

    def test_get_best_domain_empty(self):
        tracker = OutcomeTracker()
        aggregator = DomainAggregator(tracker)
        assert aggregator.get_best_domain() is None

    def test_get_worst_domain_empty(self):
        tracker = OutcomeTracker()
        aggregator = DomainAggregator(tracker)
        assert aggregator.get_worst_domain() is None

    def test_domain_summary_structure(self, tracker):
        aggregator = DomainAggregator(tracker)
        summary = aggregator.get_domain_summary()
        for domain_name, stats in summary.items():
            assert "count" in stats
            assert "success_rate" in stats
            assert "avg_reward" in stats
            assert "total_reward" in stats


class TestCharacterAggregator:
    """Tests for CharacterAggregator class."""

    @pytest.fixture
    def tracker(self):
        tracker = OutcomeTracker()
        tracker.track_immediate_outcome(
            decision_id="char1_1", description="Action by thorin", success=True,
            context={"decision_type": "combat_action", "character_id": "thorin"},
        )
        tracker.track_immediate_outcome(
            decision_id="char1_2", description="Another action by thorin", success=False,
            context={"decision_type": "social", "character_id": "thorin"},
        )
        tracker.track_immediate_outcome(
            decision_id="char2_1", description="Action by elara", success=True,
            context={"decision_type": "exploration", "character_id": "elara"},
        )
        return tracker

    def test_aggregate_by_character(self, tracker):
        aggregator = CharacterAggregator(tracker)
        results = aggregator.aggregate_by_character()
        assert "thorin" in results
        assert "elara" in results
        thorin = results["thorin"]
        assert thorin.count == 2
        assert thorin.success_count == 1

    def test_get_character_ranking(self, tracker):
        aggregator = CharacterAggregator(tracker)
        ranking = aggregator.get_character_ranking()
        assert len(ranking) == 2
        assert all(isinstance(r, tuple) and len(r) == 2 for r in ranking)

    def test_get_top_character(self, tracker):
        aggregator = CharacterAggregator(tracker)
        top = aggregator.get_top_character(1)
        assert len(top) == 1

    def test_top_character_n_greater_than_available(self, tracker):
        aggregator = CharacterAggregator(tracker)
        top = aggregator.get_top_character(10)
        assert len(top) == 2

    def test_unknown_character_id(self):
        tracker = OutcomeTracker()
        tracker.track_immediate_outcome(
            decision_id="anon", description="test", success=True, context={},
        )
        aggregator = CharacterAggregator(tracker)
        results = aggregator.aggregate_by_character()
        assert "unknown" in results

    def test_empty_tracker(self):
        tracker = OutcomeTracker()
        aggregator = CharacterAggregator(tracker)
        results = aggregator.aggregate_by_character()
        assert len(results) == 0

    def test_character_domain_breakdown(self, tracker):
        aggregator = CharacterAggregator(tracker)
        results = aggregator.aggregate_by_character()
        thorin = results["thorin"]
        assert isinstance(thorin.domain_breakdown, dict)

    def test_ranking_sorted_descending(self, tracker):
        aggregator = CharacterAggregator(tracker)
        ranking = aggregator.get_character_ranking()
        for i in range(len(ranking) - 1):
            assert ranking[i][1] >= ranking[i + 1][1]


class TestCustomAggregator:
    """Tests for CustomAggregator class."""

    @pytest.fixture
    def tracker(self):
        tracker = OutcomeTracker()
        tracker.track_immediate_outcome(
            decision_id="immediate_1", description="Immediate outcome", success=True,
            context={"decision_type": "combat_action"},
        )
        tracker.track_delayed_outcome(
            decision_id="delayed_1", description="Delayed outcome", success=True,
            context={"decision_type": "social"},
            outcome_type=OutcomeType.SHORT_TERM,
        )
        return tracker

    def test_aggregate_by_outcome_type(self, tracker):
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(key_fn=lambda o: o.outcome_type.value)
        assert "immediate" in results
        assert "short_term" in results
        assert results["immediate"].count == 1
        assert results["short_term"].count == 1

    def test_aggregate_with_filter(self, tracker):
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(
            key_fn=lambda o: o.outcome_type.value,
            filter_fn=lambda o: o.success,
        )
        assert sum(r.count for r in results.values()) == 2

    def test_aggregate_by_decision_id(self, tracker):
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(key_fn=lambda o: o.decision_id)
        assert "immediate_1" in results
        assert "delayed_1" in results

    def test_aggregate_filter_excludes_all(self, tracker):
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(
            key_fn=lambda o: o.decision_id,
            filter_fn=lambda o: False,
        )
        assert len(results) == 0

    def test_aggregate_empty_tracker(self):
        tracker = OutcomeTracker()
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(key_fn=lambda o: o.decision_id)
        assert len(results) == 0

    def test_aggregate_by_success(self, tracker):
        tracker.track_immediate_outcome(
            decision_id="fail_1", description="fail", success=False, context={},
        )
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(key_fn=lambda o: str(o.success))
        assert "True" in results
        assert "False" in results
        assert results["True"].count == 2
        assert results["False"].count == 1
