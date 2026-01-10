"""Tests for the OutcomeTracker core module."""

import pytest
import time
from outcome_tracker import (
    OutcomeTracker,
    RewardSignal,
    OutcomeRecord,
    RewardDomain,
    OutcomeType,
)


class TestOutcomeTracker:
    """Tests for OutcomeTracker class."""

    def test_init(self):
        """Test tracker initialization."""
        tracker = OutcomeTracker()
        assert tracker.outcomes == {}
        assert tracker.pending_outcomes == {}
        assert tracker.causal_chains == []
        assert tracker.metrics["total_outcomes"] == 0

    def test_track_immediate_outcome(self):
        """Test tracking immediate outcomes."""
        tracker = OutcomeTracker()

        outcome = tracker.track_immediate_outcome(
            decision_id="test_001",
            description="Hit goblin for 15 damage",
            success=True,
            context={"decision_type": "combat_action", "character_id": "thorin"},
        )

        assert outcome.decision_id == "test_001"
        assert outcome.success is True
        assert outcome.outcome_type == OutcomeType.IMMEDIATE
        assert len(outcome.rewards) > 0
        assert tracker.metrics["total_outcomes"] == 1
        assert tracker.metrics["immediate_outcomes"] == 1

    def test_track_delayed_outcome(self):
        """Test tracking delayed outcomes."""
        tracker = OutcomeTracker()

        outcome = tracker.track_delayed_outcome(
            decision_id="test_002",
            description="Gained 50 XP from combat",
            success=True,
            context={"decision_type": "combat_action"},
            outcome_type=OutcomeType.SHORT_TERM,
            related_decisions=["test_001"],
        )

        assert outcome.decision_id == "test_002"
        assert outcome.outcome_type == OutcomeType.SHORT_TERM
        assert outcome.related_decisions == ["test_001"]
        assert len(outcome.causal_chain) > 0
        assert tracker.metrics["short_term_outcomes"] == 1

    def test_combat_reward_calculation(self):
        """Test combat reward calculation."""
        tracker = OutcomeTracker()

        outcome = tracker.track_immediate_outcome(
            decision_id="combat_001",
            description="Hit goblin for 15 damage, goblin defeated",
            success=True,
            context={"decision_type": "combat_action"},
        )

        combat_rewards = [r for r in outcome.rewards if r.domain == RewardDomain.COMBAT]
        assert len(combat_rewards) > 0

        reward = combat_rewards[0]
        assert reward.value > 0  # Should be positive for success
        assert reward.confidence > 0
        assert "damage" in reward.components or "enemy_defeated" in reward.components

    def test_social_reward_calculation(self):
        """Test social reward calculation."""
        tracker = OutcomeTracker()

        outcome = tracker.track_immediate_outcome(
            decision_id="social_001",
            description="Convinced merchant, relationship improved",
            success=True,
            context={"decision_type": "social"},
        )

        social_rewards = [r for r in outcome.rewards if r.domain == RewardDomain.SOCIAL]
        assert len(social_rewards) > 0

        reward = social_rewards[0]
        assert reward.domain == RewardDomain.SOCIAL
        assert reward.value > 0

    def test_exploration_reward_calculation(self):
        """Test exploration reward calculation."""
        tracker = OutcomeTracker()

        outcome = tracker.track_immediate_outcome(
            decision_id="explore_001",
            description="Discovered hidden secret door",
            success=True,
            context={"decision_type": "exploration"},
        )

        exploration_rewards = [r for r in outcome.rewards if r.domain == RewardDomain.EXPLORATION]
        assert len(exploration_rewards) > 0

        reward = exploration_rewards[0]
        assert reward.domain == RewardDomain.EXPLORATION

    def test_resource_reward_calculation(self):
        """Test resource reward calculation."""
        tracker = OutcomeTracker()

        outcome = tracker.track_immediate_outcome(
            decision_id="resource_001",
            description="Gained 100 XP and 50 gold",
            success=True,
            context={"decision_type": "combat_action"},
        )

        resource_rewards = [r for r in outcome.rewards if r.domain == RewardDomain.RESOURCE]
        assert len(resource_rewards) > 0

        reward = resource_rewards[0]
        assert reward.domain == RewardDomain.RESOURCE
        assert reward.value > 0

    def test_get_aggregate_reward(self):
        """Test getting aggregate reward for a decision."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="agg_test",
            description="Hit for 10 damage",
            success=True,
            context={"decision_type": "combat_action"},
        )

        reward = tracker.get_aggregate_reward("agg_test")
        assert reward > 0

        # Test domain filtering
        combat_reward = tracker.get_aggregate_reward("agg_test", RewardDomain.COMBAT)
        assert combat_reward >= 0

    def test_get_success_rate(self):
        """Test getting success rates."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="sr_001",
            description="Success",
            success=True,
            context={"decision_type": "combat_action"},
        )
        tracker.track_immediate_outcome(
            decision_id="sr_002",
            description="Failure",
            success=False,
            context={"decision_type": "combat_action"},
        )
        tracker.track_immediate_outcome(
            decision_id="sr_003",
            description="Success",
            success=True,
            context={"decision_type": "social"},
        )

        overall = tracker.get_success_rate()
        assert overall == 2.0 / 3.0

        combat = tracker.get_success_rate("combat_action")
        assert combat == 0.5

    def test_get_statistics(self):
        """Test getting statistics."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="stat_001",
            description="Test",
            success=True,
            context={"decision_type": "combat_action"},
        )

        stats = tracker.get_statistics()
        assert stats["total_outcomes"] == 1
        assert stats["immediate_outcomes"] == 1
        assert "success_rate_overall" in stats
        assert "correlation_time_ms" in stats

    def test_analyze_decision_quality(self):
        """Test decision quality analysis."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="quality_001",
            description="Great success",
            success=True,
            context={"decision_type": "combat_action"},
        )

        quality = tracker.analyze_decision_quality("quality_001")

        assert "quality_score" in quality
        assert "confidence" in quality
        assert "success_rate" in quality
        assert quality["success_rate"] == 1.0
        assert quality["total_outcomes"] == 1

    def test_get_outcomes_for_decision(self):
        """Test getting outcomes for a specific decision."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="get_test",
            description="Outcome 1",
            success=True,
            context={},
        )
        tracker.track_delayed_outcome(
            decision_id="get_test",
            description="Outcome 2",
            success=True,
            context={},
            outcome_type=OutcomeType.SHORT_TERM,
        )

        outcomes = tracker.get_outcomes_for_decision("get_test")
        assert len(outcomes) == 2

        empty = tracker.get_outcomes_for_decision("nonexistent")
        assert len(empty) == 0

    def test_clear(self):
        """Test clearing the tracker."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="clear_test",
            description="Test",
            success=True,
            context={},
        )

        assert tracker.metrics["total_outcomes"] == 1

        tracker.clear()

        assert tracker.metrics["total_outcomes"] == 0
        assert len(tracker.outcomes) == 0
        assert len(tracker.causal_chains) == 0


class TestRewardSignal:
    """Tests for RewardSignal class."""

    def test_to_dict(self):
        """Test converting to dictionary."""
        signal = RewardSignal(
            domain=RewardDomain.COMBAT,
            value=0.5,
            confidence=0.8,
            components={"damage": 0.3},
            reasoning="Test reasoning",
        )

        data = signal.to_dict()
        assert data["domain"] == "combat"
        assert data["value"] == 0.5
        assert data["confidence"] == 0.8
        assert data["components"] == {"damage": 0.3}
        assert data["reasoning"] == "Test reasoning"

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "domain": "social",
            "value": 0.7,
            "confidence": 0.9,
            "components": {"trust": 0.5},
            "reasoning": "Social success",
        }

        signal = RewardSignal.from_dict(data)
        assert signal.domain == RewardDomain.SOCIAL
        assert signal.value == 0.7
        assert signal.confidence == 0.9


class TestOutcomeRecord:
    """Tests for OutcomeRecord class."""

    def test_to_dict(self):
        """Test converting to dictionary."""
        record = OutcomeRecord(
            decision_id="test_001",
            outcome_type=OutcomeType.IMMEDIATE,
            timestamp=time.time(),
            description="Test outcome",
            success=True,
            rewards=[
                RewardSignal(
                    domain=RewardDomain.COMBAT,
                    value=0.5,
                    confidence=0.8,
                )
            ],
        )

        data = record.to_dict()
        assert data["decision_id"] == "test_001"
        assert data["outcome_type"] == "immediate"
        assert data["success"] is True
        assert len(data["rewards"]) == 1

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "decision_id": "test_002",
            "outcome_type": "short_term",
            "timestamp": time.time(),
            "description": "Delayed outcome",
            "success": False,
            "rewards": [],
            "related_decisions": [],
            "causal_chain": [],
            "metadata": {},
        }

        record = OutcomeRecord.from_dict(data)
        assert record.decision_id == "test_002"
        assert record.outcome_type == OutcomeType.SHORT_TERM
        assert record.success is False


class TestEnums:
    """Tests for enum classes."""

    def test_outcome_type(self):
        """Test OutcomeType enum."""
        assert OutcomeType.IMMEDIATE.value == "immediate"
        assert OutcomeType.SHORT_TERM.value == "short_term"
        assert OutcomeType.LONG_TERM.value == "long_term"

    def test_reward_domain(self):
        """Test RewardDomain enum."""
        assert RewardDomain.COMBAT.value == "combat"
        assert RewardDomain.SOCIAL.value == "social"
        assert RewardDomain.EXPLORATION.value == "exploration"
        assert RewardDomain.RESOURCE.value == "resource"
        assert RewardDomain.STRATEGIC.value == "strategic"
