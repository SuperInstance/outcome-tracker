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
        assert reward.value > 0
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
        combat_reward = tracker.get_aggregate_reward("agg_test", RewardDomain.COMBAT)
        assert combat_reward >= 0

    def test_get_success_rate(self):
        """Test getting success rates."""
        tracker = OutcomeTracker()
        tracker.track_immediate_outcome(
            decision_id="sr_001", description="Success", success=True,
            context={"decision_type": "combat_action"},
        )
        tracker.track_immediate_outcome(
            decision_id="sr_002", description="Failure", success=False,
            context={"decision_type": "combat_action"},
        )
        tracker.track_immediate_outcome(
            decision_id="sr_003", description="Success", success=True,
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
            decision_id="stat_001", description="Test", success=True,
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
            decision_id="quality_001", description="Great success", success=True,
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
            decision_id="get_test", description="Outcome 1", success=True, context={},
        )
        tracker.track_delayed_outcome(
            decision_id="get_test", description="Outcome 2", success=True, context={},
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
            decision_id="clear_test", description="Test", success=True, context={},
        )
        assert tracker.metrics["total_outcomes"] == 1
        tracker.clear()
        assert tracker.metrics["total_outcomes"] == 0
        assert len(tracker.outcomes) == 0
        assert len(tracker.causal_chains) == 0

    def test_get_all_outcomes(self):
        """Test getting all outcomes."""
        tracker = OutcomeTracker()
        tracker.track_immediate_outcome(
            decision_id="a", description="test", success=True, context={},
        )
        tracker.track_immediate_outcome(
            decision_id="b", description="test", success=False, context={},
        )
        all_outcomes = tracker.get_all_outcomes()
        assert len(all_outcomes) == 2

    def test_track_long_term_outcome(self):
        """Test tracking long-term outcomes."""
        tracker = OutcomeTracker()
        outcome = tracker.track_delayed_outcome(
            decision_id="lt_001", description="Long-term effect", success=True,
            context={"decision_type": "strategic"},
            outcome_type=OutcomeType.LONG_TERM,
        )
        assert outcome.outcome_type == OutcomeType.LONG_TERM
        assert tracker.metrics["long_term_outcomes"] == 1

    def test_multiple_outcomes_same_decision(self):
        """Test tracking multiple outcomes for same decision."""
        tracker = OutcomeTracker()
        tracker.track_immediate_outcome(
            decision_id="multi", description="immediate", success=True,
            context={"decision_type": "combat_action"},
        )
        tracker.track_delayed_outcome(
            decision_id="multi", description="delayed", success=False, context={},
            outcome_type=OutcomeType.SHORT_TERM,
        )
        outcomes = tracker.get_outcomes_for_decision("multi")
        assert len(outcomes) == 2

    def test_aggregate_reward_nonexistent(self):
        """Test aggregate reward for nonexistent decision returns 0."""
        tracker = OutcomeTracker()
        assert tracker.get_aggregate_reward("nonexistent") == 0.0

    def test_success_rate_no_outcomes(self):
        """Test success rate returns 0 when no outcomes."""
        tracker = OutcomeTracker()
        assert tracker.get_success_rate() == 0.0

    def test_decision_quality_no_outcomes(self):
        """Test decision quality analysis with no outcomes."""
        tracker = OutcomeTracker()
        quality = tracker.analyze_decision_quality("nonexistent")
        assert quality["quality_score"] == 0.0
        assert quality["confidence"] == 0.0
        assert "No outcomes available" in quality["reasoning"]

    def test_combat_damage_taken_negative(self):
        """Test that taking damage gives negative reward component."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="dmg_taken", description="Took 20 damage in combat",
            success=False, context={"decision_type": "combat_action"},
        )
        combat_rewards = [r for r in outcome.rewards if r.domain == RewardDomain.COMBAT]
        if combat_rewards:
            assert "damage_taken" in combat_rewards[0].components
            assert combat_rewards[0].components["damage_taken"] < 0

    def test_strategic_reward_for_success(self):
        """Test strategic reward is generated for successful outcomes."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="strat_001", description="Advanced position", success=True,
            context={"decision_type": "strategic"},
        )
        strategic_rewards = [r for r in outcome.rewards if r.domain == RewardDomain.STRATEGIC]
        assert len(strategic_rewards) > 0

    def test_causal_chain_building(self):
        """Test causal chain is built with related decisions."""
        tracker = OutcomeTracker()
        outcome = tracker.track_delayed_outcome(
            decision_id="c_003", description="Result", success=True, context={},
            outcome_type=OutcomeType.SHORT_TERM,
            related_decisions=["c_001", "c_002"],
        )
        assert "c_001" in outcome.causal_chain
        assert "c_002" in outcome.causal_chain
        assert "c_003" in outcome.causal_chain
        assert len(tracker.causal_chains) > 0

    def test_statistics_include_causal_chains(self):
        """Test statistics include causal chain info."""
        tracker = OutcomeTracker()
        tracker.track_delayed_outcome(
            decision_id="cc_003", description="test", success=True, context={},
            outcome_type=OutcomeType.SHORT_TERM,
            related_decisions=["cc_001", "cc_002"],
        )
        stats = tracker.get_statistics()
        assert stats["total_causal_chains"] > 0
        assert "avg_chain_length" in stats

    def test_outcome_timestamp_is_recent(self):
        """Test outcome timestamps are recent."""
        tracker = OutcomeTracker()
        before = time.time()
        outcome = tracker.track_immediate_outcome(
            decision_id="ts_test", description="test", success=True, context={},
        )
        after = time.time()
        assert before <= outcome.timestamp <= after

    def test_metadata_stored_with_outcome(self):
        """Test metadata is stored alongside outcomes."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="meta_test", description="test", success=True,
            context={"decision_type": "combat_action", "character_id": "hero", "level": 5},
        )
        assert outcome.metadata["context"]["character_id"] == "hero"
        assert outcome.metadata["context"]["level"] == 5

    def test_immediate_outcome_no_causal_chain(self):
        """Test immediate outcomes have empty causal chain."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="no_chain", description="test", success=True, context={},
        )
        assert outcome.causal_chain == []

    def test_tactical_advantage_combat(self):
        """Test tactical advantage keywords detected in combat."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="flank", description="Flanked enemy for critical hit",
            success=True, context={"decision_type": "combat_action"},
        )
        combat = [r for r in outcome.rewards if r.domain == RewardDomain.COMBAT]
        if combat:
            assert "tactical_advantage" in combat[0].components

    def test_party_safety_combat(self):
        """Test party safety keyword detected in combat."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="safe", description="Party safe after encounter",
            success=True, context={"decision_type": "combat_action"},
        )
        combat = [r for r in outcome.rewards if r.domain == RewardDomain.COMBAT]
        if combat:
            assert "party_safety" in combat[0].components

    def test_trust_social_reward(self):
        """Test trust keyword in social reward."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="trust_001", description="Built trust with NPC",
            success=True, context={"decision_type": "social"},
        )
        social = [r for r in outcome.rewards if r.domain == RewardDomain.SOCIAL]
        assert len(social) > 0

    def test_exploration_danger_avoided(self):
        """Test danger avoided keyword in exploration reward."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="avoid", description="Avoided trap, stayed safe",
            success=True, context={"decision_type": "exploration"},
        )
        explore = [r for r in outcome.rewards if r.domain == RewardDomain.EXPLORATION]
        assert len(explore) > 0

    def test_resource_consumed_negative(self):
        """Test resource consumption gives negative component."""
        tracker = OutcomeTracker()
        outcome = tracker.track_immediate_outcome(
            decision_id="consume", description="Used healing potion, gained 10 XP",
            success=True, context={"decision_type": "exploration"},
        )
        resource = [r for r in outcome.rewards if r.domain == RewardDomain.RESOURCE]
        if resource:
            assert "resources_spent" in resource[0].components


class TestRewardSignal:
    """Tests for RewardSignal class."""

    def test_to_dict(self):
        signal = RewardSignal(
            domain=RewardDomain.COMBAT, value=0.5, confidence=0.8,
            components={"damage": 0.3}, reasoning="Test reasoning",
        )
        data = signal.to_dict()
        assert data["domain"] == "combat"
        assert data["value"] == 0.5
        assert data["confidence"] == 0.8
        assert data["components"] == {"damage": 0.3}
        assert data["reasoning"] == "Test reasoning"

    def test_from_dict(self):
        data = {
            "domain": "social", "value": 0.7, "confidence": 0.9,
            "components": {"trust": 0.5}, "reasoning": "Social success",
        }
        signal = RewardSignal.from_dict(data)
        assert signal.domain == RewardDomain.SOCIAL
        assert signal.value == 0.7
        assert signal.confidence == 0.9

    def test_from_dict_defaults(self):
        """Test from_dict with minimal data uses defaults."""
        data = {"domain": "resource", "value": 0.3, "confidence": 0.5}
        signal = RewardSignal.from_dict(data)
        assert signal.components == {}
        assert signal.reasoning == ""

    def test_to_dict_roundtrip(self):
        """Test to_dict -> from_dict roundtrip."""
        original = RewardSignal(
            domain=RewardDomain.STRATEGIC, value=-0.5, confidence=0.6,
            components={"positioning": -0.3}, reasoning="Bad move",
        )
        restored = RewardSignal.from_dict(original.to_dict())
        assert restored.domain == original.domain
        assert restored.value == original.value
        assert restored.confidence == original.confidence
        assert restored.components == original.components

    def test_all_domains_valid(self):
        """Test all reward domains can be created."""
        for domain in RewardDomain:
            signal = RewardSignal(domain=domain, value=0.5, confidence=0.5)
            assert signal.domain == domain

    def test_negative_value(self):
        """Test reward signal with negative value."""
        signal = RewardSignal(domain=RewardDomain.COMBAT, value=-0.8, confidence=0.9)
        assert signal.value < 0


class TestOutcomeRecord:
    """Tests for OutcomeRecord class."""

    def test_to_dict(self):
        record = OutcomeRecord(
            decision_id="test_001", outcome_type=OutcomeType.IMMEDIATE,
            timestamp=time.time(), description="Test outcome", success=True,
            rewards=[RewardSignal(domain=RewardDomain.COMBAT, value=0.5, confidence=0.8)],
        )
        data = record.to_dict()
        assert data["decision_id"] == "test_001"
        assert data["outcome_type"] == "immediate"
        assert data["success"] is True
        assert len(data["rewards"]) == 1

    def test_from_dict(self):
        data = {
            "decision_id": "test_002", "outcome_type": "short_term",
            "timestamp": time.time(), "description": "Delayed outcome",
            "success": False, "rewards": [], "related_decisions": [],
            "causal_chain": [], "metadata": {},
        }
        record = OutcomeRecord.from_dict(data)
        assert record.decision_id == "test_002"
        assert record.outcome_type == OutcomeType.SHORT_TERM
        assert record.success is False

    def test_from_dict_with_rewards(self):
        """Test from_dict with reward data."""
        data = {
            "decision_id": "test_003", "outcome_type": "immediate",
            "timestamp": time.time(), "description": "test", "success": True,
            "rewards": [{"domain": "combat", "value": 0.5, "confidence": 0.8,
                         "components": {}, "reasoning": ""}],
            "related_decisions": [], "causal_chain": [], "metadata": {},
        }
        record = OutcomeRecord.from_dict(data)
        assert len(record.rewards) == 1
        assert record.rewards[0].domain == RewardDomain.COMBAT

    def test_roundtrip(self):
        """Test to_dict -> from_dict roundtrip."""
        original = OutcomeRecord(
            decision_id="rt_001", outcome_type=OutcomeType.LONG_TERM,
            timestamp=12345.0, description="test", success=False,
            related_decisions=["a", "b"], causal_chain=["a", "b", "rt_001"],
            metadata={"key": "value"},
        )
        restored = OutcomeRecord.from_dict(original.to_dict())
        assert restored.decision_id == original.decision_id
        assert restored.outcome_type == original.outcome_type
        assert restored.success == original.success
        assert restored.related_decisions == original.related_decisions
        assert restored.metadata == original.metadata


class TestEnums:
    """Tests for enum classes."""

    def test_outcome_type(self):
        assert OutcomeType.IMMEDIATE.value == "immediate"
        assert OutcomeType.SHORT_TERM.value == "short_term"
        assert OutcomeType.LONG_TERM.value == "long_term"

    def test_reward_domain(self):
        assert RewardDomain.COMBAT.value == "combat"
        assert RewardDomain.SOCIAL.value == "social"
        assert RewardDomain.EXPLORATION.value == "exploration"
        assert RewardDomain.RESOURCE.value == "resource"
        assert RewardDomain.STRATEGIC.value == "strategic"

    def test_outcome_type_members(self):
        assert len(OutcomeType) == 3

    def test_reward_domain_members(self):
        assert len(RewardDomain) == 5

    def test_enum_iteration(self):
        domains = list(RewardDomain)
        assert len(domains) == 5
        assert all(isinstance(d, RewardDomain) for d in domains)
