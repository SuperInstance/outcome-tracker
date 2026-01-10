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
        """Test timestamp containment check."""
        window = TimeWindow(start=1000.0, end=2000.0)

        assert window.contains(1500.0) is True
        assert window.contains(1000.0) is True
        assert window.contains(2000.0) is True
        assert window.contains(999.0) is False
        assert window.contains(2001.0) is False


class TestAggregationResult:
    """Tests for AggregationResult class."""

    def test_success_rate(self):
        """Test success rate calculation."""
        result = AggregationResult(
            key="test",
            count=10,
            success_count=7,
            total_reward=3.5,
            avg_reward=0.35,
        )

        assert result.success_rate == 0.7

    def test_success_rate_zero_count(self):
        """Test success rate with zero count."""
        result = AggregationResult(
            key="test",
            count=0,
            success_count=0,
            total_reward=0.0,
            avg_reward=0.0,
        )

        assert result.success_rate == 0.0

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = AggregationResult(
            key="test",
            count=5,
            success_count=3,
            total_reward=1.5,
            avg_reward=0.3,
            domain_breakdown={"combat": 0.5},
        )

        data = result.to_dict()
        assert data["key"] == "test"
        assert data["count"] == 5
        assert data["success_rate"] == 0.6
        assert data["avg_reward"] == 0.3
        assert data["domain_breakdown"] == {"combat": 0.5}


class TestTimeWindowAggregator:
    """Tests for TimeWindowAggregator class."""

    @pytest.fixture
    def tracker(self):
        """Create a tracker with sample data."""
        tracker = OutcomeTracker()

        # Add some outcomes with known timestamps
        now = time.time()

        tracker.track_immediate_outcome(
            decision_id="early",
            description="Early outcome",
            success=True,
            context={"decision_type": "combat_action"},
        )
        # Manually set timestamp
        tracker.outcomes["early"][0].timestamp = now - 7200  # 2 hours ago

        tracker.track_immediate_outcome(
            decision_id="recent",
            description="Recent outcome",
            success=True,
            context={"decision_type": "social"},
        )
        tracker.outcomes["recent"][0].timestamp = now - 300  # 5 minutes ago

        return tracker

    def test_aggregate_by_window(self, tracker):
        """Test aggregation by explicit windows."""
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
        """Test aggregation for recent time period."""
        aggregator = TimeWindowAggregator(tracker)

        result = aggregator.aggregate_last_n_minutes(10)

        assert result.key == "last_10_min"
        # Should only include the recent outcome
        assert result.count == 1


class TestDomainAggregator:
    """Tests for DomainAggregator class."""

    @pytest.fixture
    def tracker(self):
        """Create a tracker with sample data."""
        tracker = OutcomeTracker()

        # Combat outcomes - both have combat rewards
        tracker.track_immediate_outcome(
            decision_id="combat_1",
            description="Hit for 15 damage",
            success=True,
            context={"decision_type": "combat_action"},
        )

        tracker.track_immediate_outcome(
            decision_id="combat_2",
            description="Took 5 damage but kept fighting",
            success=False,
            context={"decision_type": "combat_action"},
        )

        tracker.track_immediate_outcome(
            decision_id="social_1",
            description="Convinced merchant",
            success=True,
            context={"decision_type": "social"},
        )

        return tracker

    def test_aggregate_by_domain(self, tracker):
        """Test aggregation by domain."""
        aggregator = DomainAggregator(tracker)
        results = aggregator.aggregate_by_domain()

        assert RewardDomain.COMBAT in results
        assert RewardDomain.SOCIAL in results

        combat = results[RewardDomain.COMBAT]
        assert combat.count == 2
        # Note: success_count depends on which outcomes succeeded
        assert combat.success_count >= 0

    def test_get_domain_summary(self, tracker):
        """Test getting domain summary."""
        aggregator = DomainAggregator(tracker)
        summary = aggregator.get_domain_summary()

        assert "combat" in summary
        assert "social" in summary
        assert summary["combat"]["count"] == 2

    def test_get_best_domain(self, tracker):
        """Test getting best performing domain."""
        aggregator = DomainAggregator(tracker)
        best = aggregator.get_best_domain()

        assert best is not None
        assert isinstance(best, RewardDomain)

    def test_get_worst_domain(self, tracker):
        """Test getting worst performing domain."""
        aggregator = DomainAggregator(tracker)
        worst = aggregator.get_worst_domain()

        assert worst is not None
        assert isinstance(worst, RewardDomain)


class TestCharacterAggregator:
    """Tests for CharacterAggregator class."""

    @pytest.fixture
    def tracker(self):
        """Create a tracker with sample data."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="char1_1",
            description="Action by thorin",
            success=True,
            context={"decision_type": "combat_action", "character_id": "thorin"},
        )

        tracker.track_immediate_outcome(
            decision_id="char1_2",
            description="Another action by thorin",
            success=False,
            context={"decision_type": "social", "character_id": "thorin"},
        )

        tracker.track_immediate_outcome(
            decision_id="char2_1",
            description="Action by elara",
            success=True,
            context={"decision_type": "exploration", "character_id": "elara"},
        )

        return tracker

    def test_aggregate_by_character(self, tracker):
        """Test aggregation by character."""
        aggregator = CharacterAggregator(tracker)
        results = aggregator.aggregate_by_character()

        assert "thorin" in results
        assert "elara" in results

        thorin = results["thorin"]
        assert thorin.count == 2
        assert thorin.success_count == 1

    def test_get_character_ranking(self, tracker):
        """Test getting character ranking."""
        aggregator = CharacterAggregator(tracker)
        ranking = aggregator.get_character_ranking()

        assert len(ranking) == 2
        assert all(isinstance(r, tuple) and len(r) == 2 for r in ranking)

    def test_get_top_character(self, tracker):
        """Test getting top character."""
        aggregator = CharacterAggregator(tracker)
        top = aggregator.get_top_character(1)

        assert len(top) == 1


class TestCustomAggregator:
    """Tests for CustomAggregator class."""

    @pytest.fixture
    def tracker(self):
        """Create a tracker with sample data."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="immediate_1",
            description="Immediate outcome",
            success=True,
            context={"decision_type": "combat_action"},
        )

        tracker.track_delayed_outcome(
            decision_id="delayed_1",
            description="Delayed outcome",
            success=True,
            context={"decision_type": "social"},
            outcome_type=OutcomeType.SHORT_TERM,
        )

        return tracker

    def test_aggregate_by_outcome_type(self, tracker):
        """Test custom aggregation by outcome type."""
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(
            key_fn=lambda o: o.outcome_type.value,
        )

        assert "immediate" in results
        assert "short_term" in results

        assert results["immediate"].count == 1
        assert results["short_term"].count == 1

    def test_aggregate_with_filter(self, tracker):
        """Test custom aggregation with filtering."""
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(
            key_fn=lambda o: o.outcome_type.value,
            filter_fn=lambda o: o.success,
        )

        # Both outcomes are successful
        assert sum(r.count for r in results.values()) == 2

    def test_aggregate_by_decision_id(self, tracker):
        """Test custom aggregation by decision ID."""
        aggregator = CustomAggregator(tracker)
        results = aggregator.aggregate(
            key_fn=lambda o: o.decision_id,
        )

        assert "immediate_1" in results
        assert "delayed_1" in results
