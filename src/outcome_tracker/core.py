"""
Outcome Tracker Core Module

This module contains the core OutcomeTracker class and associated data structures
for tracking decision outcomes with sophisticated reward signals.
"""

import time
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Types of outcomes based on temporal correlation.

    Attributes:
        IMMEDIATE: Happens right away (hit/miss, accept/reject)
        SHORT_TERM: Within same encounter (5-10 turns)
        LONG_TERM: Multiple encounters (session-wide)
    """
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class RewardDomain(Enum):
    """Domains for reward calculation.

    Each domain represents a different aspect of agent behavior and outcomes.

    Attributes:
        COMBAT: Combat-related outcomes (damage, defeats, tactical advantage)
        SOCIAL: Social interaction outcomes (relationships, persuasion, trust)
        EXPLORATION: Discovery and exploration outcomes (secrets, discoveries)
        RESOURCE: Resource acquisition and consumption (XP, gold, items)
        STRATEGIC: Long-term positioning and goal progress
    """
    COMBAT = "combat"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    RESOURCE = "resource"
    STRATEGIC = "strategic"


@dataclass
class RewardSignal:
    """A calculated reward signal for an outcome.

    Reward signals represent the value of an outcome in a specific domain,
    with a confidence score and detailed component breakdown.

    Attributes:
        domain: The reward domain this signal belongs to
        value: The reward value, normalized to [-1.0, 1.0]
        confidence: Confidence in this reward calculation [0.0, 1.0]
        components: Dictionary of component values that sum to the total
        reasoning: Human-readable explanation of the reward calculation
    """
    domain: RewardDomain
    value: float
    confidence: float
    components: Dict[str, float] = field(default_factory=dict)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing all reward signal data
        """
        return {
            "domain": self.domain.value,
            "value": self.value,
            "confidence": self.confidence,
            "components": self.components,
            "reasoning": self.reasoning,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RewardSignal":
        """Create a RewardSignal from a dictionary.

        Args:
            data: Dictionary containing reward signal data

        Returns:
            A new RewardSignal instance
        """
        return cls(
            domain=RewardDomain(data["domain"]),
            value=data["value"],
            confidence=data["confidence"],
            components=data.get("components", {}),
            reasoning=data.get("reasoning", ""),
        )


@dataclass
class OutcomeRecord:
    """A record of a decision outcome.

    Outcome records store all information about a specific outcome, including
    its type, success status, reward signals, and causal relationships.

    Attributes:
        decision_id: ID of the decision that led to this outcome
        outcome_type: Temporal type of the outcome
        timestamp: Unix timestamp when the outcome occurred
        description: Human-readable description of what happened
        success: Whether the outcome was successful
        rewards: List of reward signals for this outcome
        related_decisions: IDs of other decisions related to this outcome
        causal_chain: Ordered chain of decisions leading to this outcome
        metadata: Additional context and metadata
    """
    decision_id: str
    outcome_type: OutcomeType
    timestamp: float
    description: str
    success: bool
    rewards: List[RewardSignal] = field(default_factory=list)
    related_decisions: List[str] = field(default_factory=list)
    causal_chain: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing all outcome record data
        """
        return {
            "decision_id": self.decision_id,
            "outcome_type": self.outcome_type.value,
            "timestamp": self.timestamp,
            "description": self.description,
            "success": self.success,
            "rewards": [r.to_dict() for r in self.rewards],
            "related_decisions": self.related_decisions,
            "causal_chain": self.causal_chain,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutcomeRecord":
        """Create an OutcomeRecord from a dictionary.

        Args:
            data: Dictionary containing outcome record data

        Returns:
            A new OutcomeRecord instance
        """
        return cls(
            decision_id=data["decision_id"],
            outcome_type=OutcomeType(data["outcome_type"]),
            timestamp=data["timestamp"],
            description=data["description"],
            success=data["success"],
            rewards=[
                RewardSignal.from_dict(r) for r in data.get("rewards", [])
            ],
            related_decisions=data.get("related_decisions", []),
            causal_chain=data.get("causal_chain", []),
            metadata=data.get("metadata", {}),
        )


class OutcomeTracker:
    """Tracks and analyzes decision outcomes with multi-domain reward signals.

    The OutcomeTracker provides sophisticated tracking of decision outcomes across
    multiple domains, with temporal correlation analysis and causal chain tracking.

    Features:
        - Temporal correlation (immediate, short-term, long-term outcomes)
        - Multi-domain reward calculation (combat, social, exploration, resource, strategic)
        - Causal chain tracking (decision -> outcome -> consequence)
        - Performance metrics and statistics
        - Decision quality analysis

    Example:
        >>> tracker = OutcomeTracker()
        >>> outcome = tracker.track_immediate_outcome(
        ...     decision_id="combat_001",
        ...     description="Hit goblin for 15 damage",
        ...     success=True,
        ...     context={"decision_type": "combat_action"}
        ... )
        >>> quality = tracker.analyze_decision_quality("combat_001")
    """

    def __init__(self) -> None:
        """Initialize the outcome tracker."""
        # Storage
        self.outcomes: Dict[str, List[OutcomeRecord]] = {}
        self.pending_outcomes: Dict[str, Dict[str, Any]] = {}
        self.causal_chains: List[List[str]] = []

        # Performance metrics
        self.metrics: Dict[str, Any] = {
            "total_outcomes": 0,
            "immediate_outcomes": 0,
            "short_term_outcomes": 0,
            "long_term_outcomes": 0,
            "avg_reward_signal": 0.0,
            "correlation_time_ms": 0.0,
        }

        logger.info("OutcomeTracker initialized")

    def track_immediate_outcome(
        self,
        decision_id: str,
        description: str,
        success: bool,
        context: Dict[str, Any],
    ) -> OutcomeRecord:
        """Track an immediate outcome that happens right after a decision.

        Args:
            decision_id: ID of the decision
            description: What happened
            success: Whether the outcome was successful
            context: Decision context for reward calculation

        Returns:
            The created OutcomeRecord
        """
        start_time = time.time()

        rewards = self._calculate_rewards(context, description, success)

        outcome = OutcomeRecord(
            decision_id=decision_id,
            outcome_type=OutcomeType.IMMEDIATE,
            timestamp=time.time(),
            description=description,
            success=success,
            rewards=rewards,
            metadata={"context": context},
        )

        self._store_outcome(outcome)
        self._update_immediate_metrics(rewards, start_time)

        logger.debug(
            f"Tracked immediate outcome for {decision_id}: "
            f"{'success' if success else 'failure'}"
        )

        return outcome

    def track_delayed_outcome(
        self,
        decision_id: str,
        description: str,
        success: bool,
        context: Dict[str, Any],
        outcome_type: OutcomeType = OutcomeType.SHORT_TERM,
        related_decisions: Optional[List[str]] = None,
    ) -> OutcomeRecord:
        """Track a delayed outcome that happens after some time.

        Args:
            decision_id: Original decision ID
            description: What happened
            success: Whether the outcome was successful
            context: Context for reward calculation
            outcome_type: SHORT_TERM or LONG_TERM
            related_decisions: Other decisions that contributed

        Returns:
            The created OutcomeRecord
        """
        start_time = time.time()

        rewards = self._calculate_rewards(context, description, success)

        outcome = OutcomeRecord(
            decision_id=decision_id,
            outcome_type=outcome_type,
            timestamp=time.time(),
            description=description,
            success=success,
            rewards=rewards,
            related_decisions=related_decisions or [],
            metadata={"context": context},
        )

        if related_decisions:
            outcome.causal_chain = self._build_causal_chain(
                decision_id,
                related_decisions,
            )

        self._store_outcome(outcome)
        self._update_delayed_metrics(outcome_type, rewards, start_time)

        logger.debug(f"Tracked {outcome_type.value} outcome for {decision_id}")

        return outcome

    def _calculate_rewards(
        self,
        context: Dict[str, Any],
        description: str,
        success: bool,
    ) -> List[RewardSignal]:
        """Calculate reward signals across multiple domains.

        Args:
            context: Decision context
            description: Outcome description
            success: Whether the outcome was successful

        Returns:
            List of reward signals
        """
        rewards: List[RewardSignal] = []
        decision_type = context.get("decision_type", "unknown")
        desc_lower = description.lower()

        # Combat rewards
        if decision_type == "combat_action" or "combat" in desc_lower:
            combat_reward = self._calculate_combat_reward(
                context, description, success
            )
            if combat_reward:
                rewards.append(combat_reward)

        # Social rewards
        if decision_type == "social" or any(
            w in desc_lower for w in ["persuade", "negotiate", "relationship", "trust"]
        ):
            social_reward = self._calculate_social_reward(
                context, description, success
            )
            if social_reward:
                rewards.append(social_reward)

        # Exploration rewards
        if decision_type == "exploration" or any(
            w in desc_lower for w in ["discover", "investigate", "explore", "find"]
        ):
            exploration_reward = self._calculate_exploration_reward(
                context, description, success
            )
            if exploration_reward:
                rewards.append(exploration_reward)

        # Resource rewards
        if any(w in desc_lower for w in ["gold", "item", "xp", "reward"]):
            resource_reward = self._calculate_resource_reward(
                context, description, success
            )
            if resource_reward:
                rewards.append(resource_reward)

        # Strategic rewards
        strategic_reward = self._calculate_strategic_reward(
            context, description, success
        )
        if strategic_reward:
            rewards.append(strategic_reward)

        return rewards

    def _calculate_combat_reward(
        self,
        context: Dict[str, Any],
        description: str,
        success: bool,
    ) -> Optional[RewardSignal]:
        """Calculate combat reward signal."""
        components: Dict[str, float] = {}
        desc_lower = description.lower()

        # Damage dealt
        match = re.search(r"(\d+)\s+damage", desc_lower)
        if match:
            damage = float(match.group(1))
            components["damage_dealt"] = min(damage / 20.0, 1.0)

        # Damage taken (negative)
        match = re.search(r"took\s+(\d+)", desc_lower)
        if match:
            damage = float(match.group(1))
            components["damage_taken"] = -min(damage / 30.0, 1.0)

        # Tactical advantage
        if any(w in desc_lower for w in ["flank", "advantage", "critical"]):
            components["tactical_advantage"] = 0.3

        # Enemy defeated
        if any(w in desc_lower for w in ["defeated", "killed"]):
            components["enemy_defeated"] = 0.5

        # Party safety
        if "party safe" in desc_lower:
            components["party_safety"] = 0.3

        if not components:
            return None

        value = max(-1.0, min(1.0, sum(components.values())))

        if success:
            value = max(value, 0.3)

        return RewardSignal(
            domain=RewardDomain.COMBAT,
            value=value,
            confidence=0.8,
            components=components,
            reasoning=f"Combat outcome: {description[:50]}...",
        )

    def _calculate_social_reward(
        self,
        context: Dict[str, Any],
        description: str,
        success: bool,
    ) -> Optional[RewardSignal]:
        """Calculate social reward signal."""
        components: Dict[str, float] = {}
        desc_lower = description.lower()

        if "relationship" in desc_lower:
            if "improved" in desc_lower or "+" in description:
                components["relationship_gain"] = 0.4
            elif "worsened" in desc_lower or "-" in description:
                components["relationship_loss"] = -0.4

        if any(w in desc_lower for w in ["learned", "discovered", "told"]):
            components["information_gained"] = 0.3

        if "trust" in desc_lower:
            components["trust"] = 0.3 if success else -0.3

        if any(w in desc_lower for w in ["convinced", "agreed"]):
            components["persuasion_success"] = 0.5

        if any(w in desc_lower for w in ["resolved", "peace"]):
            components["conflict_resolution"] = 0.4

        if not components:
            return None

        value = max(-1.0, min(1.0, sum(components.values())))

        return RewardSignal(
            domain=RewardDomain.SOCIAL,
            value=value,
            confidence=0.7,
            components=components,
            reasoning=f"Social outcome: {description[:50]}...",
        )

    def _calculate_exploration_reward(
        self,
        context: Dict[str, Any],
        description: str,
        success: bool,
    ) -> Optional[RewardSignal]:
        """Calculate exploration reward signal."""
        components: Dict[str, float] = {}
        desc_lower = description.lower()

        if any(w in desc_lower for w in ["found", "discovered", "uncovered"]):
            components["discovery"] = 0.5

        if any(w in desc_lower for w in ["progress", "closer"]):
            components["progress"] = 0.3

        if any(w in desc_lower for w in ["avoided", "safe"]):
            components["danger_avoided"] = 0.2

        if any(w in desc_lower for w in ["secret", "hidden"]):
            components["secret_revealed"] = 0.4

        if any(w in desc_lower for w in ["map", "path"]):
            components["map_knowledge"] = 0.2

        if not components:
            return None

        value = max(-1.0, min(1.0, sum(components.values())))

        return RewardSignal(
            domain=RewardDomain.EXPLORATION,
            value=value,
            confidence=0.75,
            components=components,
            reasoning=f"Exploration outcome: {description[:50]}...",
        )

    def _calculate_resource_reward(
        self,
        context: Dict[str, Any],
        description: str,
        success: bool,
    ) -> Optional[RewardSignal]:
        """Calculate resource reward signal."""
        components: Dict[str, float] = {}
        desc_lower = description.lower()

        match = re.search(r"(\d+)\s*xp", desc_lower)
        if match:
            xp = float(match.group(1))
            components["xp_gained"] = min(xp / 100.0, 1.0)

        if any(w in desc_lower for w in ["gold", "treasure"]):
            components["wealth_gained"] = 0.4

        if any(w in desc_lower for w in ["item", "equipment"]):
            components["items_gained"] = 0.3

        if any(w in desc_lower for w in ["used", "consumed"]):
            components["resources_spent"] = -0.2

        if not components:
            return None

        value = max(-1.0, min(1.0, sum(components.values())))

        return RewardSignal(
            domain=RewardDomain.RESOURCE,
            value=value,
            confidence=0.9,
            components=components,
            reasoning=f"Resource outcome: {description[:50]}...",
        )

    def _calculate_strategic_reward(
        self,
        context: Dict[str, Any],
        description: str,
        success: bool,
    ) -> Optional[RewardSignal]:
        """Calculate strategic reward signal."""
        components: Dict[str, float] = {}
        desc_lower = description.lower()

        if any(w in desc_lower for w in ["position", "advantage"]):
            components["positioning"] = 0.3 if success else -0.2

        if any(w in desc_lower for w in ["opportunity", "opens"]):
            components["opportunities_created"] = 0.4

        if any(w in desc_lower for w in ["safe", "secure"]):
            components["risk_mitigation"] = 0.3

        if any(w in desc_lower for w in ["goal", "objective"]):
            components["goal_progress"] = 0.5 if success else -0.3

        if not components:
            if success:
                components["base_strategic"] = 0.2
            else:
                return None

        value = max(-1.0, min(1.0, sum(components.values())))

        return RewardSignal(
            domain=RewardDomain.STRATEGIC,
            value=value,
            confidence=0.6,
            components=components,
            reasoning=f"Strategic outcome: {description[:50]}...",
        )

    def _build_causal_chain(
        self,
        decision_id: str,
        related_decisions: List[str],
    ) -> List[str]:
        """Build causal chain showing how decisions led to this outcome.

        Args:
            decision_id: Current decision
            related_decisions: Other contributing decisions

        Returns:
            Ordered list of decision IDs forming causal chain
        """
        chain = list(related_decisions)

        if decision_id not in chain:
            chain.append(decision_id)

        if chain not in self.causal_chains:
            self.causal_chains.append(chain)

        return chain

    def _store_outcome(self, outcome: OutcomeRecord) -> None:
        """Store an outcome record.

        Args:
            outcome: The outcome to store
        """
        decision_id = outcome.decision_id
        if decision_id not in self.outcomes:
            self.outcomes[decision_id] = []
        self.outcomes[decision_id].append(outcome)
        self.metrics["total_outcomes"] += 1

    def _update_immediate_metrics(
        self,
        rewards: List[RewardSignal],
        start_time: float,
    ) -> None:
        """Update metrics for immediate outcomes.

        Args:
            rewards: List of reward signals
            start_time: Start time for correlation calculation
        """
        self.metrics["immediate_outcomes"] += 1
        self._update_reward_metrics(rewards)

        correlation_time = (time.time() - start_time) * 1000
        self.metrics["correlation_time_ms"] = (
            self.metrics["correlation_time_ms"] * 0.9 + correlation_time * 0.1
        )

    def _update_delayed_metrics(
        self,
        outcome_type: OutcomeType,
        rewards: List[RewardSignal],
        start_time: float,
    ) -> None:
        """Update metrics for delayed outcomes.

        Args:
            outcome_type: Type of outcome
            rewards: List of reward signals
            start_time: Start time for correlation calculation
        """
        if outcome_type == OutcomeType.SHORT_TERM:
            self.metrics["short_term_outcomes"] += 1
        else:
            self.metrics["long_term_outcomes"] += 1

        self._update_reward_metrics(rewards)

        correlation_time = (time.time() - start_time) * 1000
        self.metrics["correlation_time_ms"] = (
            self.metrics["correlation_time_ms"] * 0.9 + correlation_time * 0.1
        )

    def _update_reward_metrics(self, rewards: List[RewardSignal]) -> None:
        """Update average reward metrics.

        Args:
            rewards: List of reward signals
        """
        if not rewards:
            return

        avg_reward = sum(r.value for r in rewards) / len(rewards)

        total = self.metrics["total_outcomes"]
        current_avg = self.metrics["avg_reward_signal"]

        self.metrics["avg_reward_signal"] = (
            (current_avg * (total - 1) + avg_reward) / total
        )

    def get_outcomes_for_decision(self, decision_id: str) -> List[OutcomeRecord]:
        """Get all outcomes for a specific decision.

        Args:
            decision_id: Decision ID

        Returns:
            List of outcome records for the decision
        """
        return self.outcomes.get(decision_id, [])

    def get_aggregate_reward(
        self,
        decision_id: str,
        domain: Optional[RewardDomain] = None,
    ) -> float:
        """Get aggregate reward for a decision.

        Args:
            decision_id: Decision ID
            domain: Optional domain filter

        Returns:
            Aggregate reward value
        """
        outcomes = self.get_outcomes_for_decision(decision_id)

        if not outcomes:
            return 0.0

        rewards: List[float] = []
        for outcome in outcomes:
            for reward in outcome.rewards:
                if domain is None or reward.domain == domain:
                    rewards.append(reward.value * reward.confidence)

        if not rewards:
            return 0.0

        return sum(rewards) / len(rewards)

    def get_success_rate(self, decision_type: Optional[str] = None) -> float:
        """Get overall success rate.

        Args:
            decision_type: Optional filter by decision type

        Returns:
            Success rate (0.0 to 1.0)
        """
        total = 0
        successes = 0

        for decision_outcomes in self.outcomes.values():
            for outcome in decision_outcomes:
                if decision_type:
                    if outcome.metadata.get("context", {}).get("decision_type") != decision_type:
                        continue

                total += 1
                if outcome.success:
                    successes += 1

        if total == 0:
            return 0.0

        return successes / total

    def get_statistics(self) -> Dict[str, Any]:
        """Get outcome tracking statistics.

        Returns:
            Dictionary containing all statistics
        """
        stats = dict(self.metrics)

        # Add success rates by type
        stats["success_rate_overall"] = self.get_success_rate()
        stats["success_rate_combat"] = self.get_success_rate("combat_action")
        stats["success_rate_social"] = self.get_success_rate("social")
        stats["success_rate_exploration"] = self.get_success_rate("exploration")

        # Outcome type distribution
        total = self.metrics["total_outcomes"]
        if total > 0:
            stats["immediate_pct"] = self.metrics["immediate_outcomes"] / total
            stats["short_term_pct"] = self.metrics["short_term_outcomes"] / total
            stats["long_term_pct"] = self.metrics["long_term_outcomes"] / total

        # Causal chain stats
        stats["total_causal_chains"] = len(self.causal_chains)
        if self.causal_chains:
            chain_lengths = [len(chain) for chain in self.causal_chains]
            stats["avg_chain_length"] = sum(chain_lengths) / len(chain_lengths)
            stats["max_chain_length"] = max(chain_lengths)

        return stats

    def analyze_decision_quality(self, decision_id: str) -> Dict[str, Any]:
        """Analyze the quality of a decision based on its outcomes.

        Args:
            decision_id: Decision ID

        Returns:
            Analysis dictionary with quality score, confidence, and reasoning
        """
        outcomes = self.get_outcomes_for_decision(decision_id)

        if not outcomes:
            return {
                "quality_score": 0.0,
                "confidence": 0.0,
                "reasoning": "No outcomes available",
            }

        # Aggregate rewards by domain
        domain_rewards: Dict[RewardDomain, List[float]] = {}
        for outcome in outcomes:
            for reward in outcome.rewards:
                if reward.domain not in domain_rewards:
                    domain_rewards[reward.domain] = []
                domain_rewards[reward.domain].append(reward.value * reward.confidence)

        # Calculate average per domain
        domain_scores = {
            domain.value: sum(rewards) / len(rewards)
            for domain, rewards in domain_rewards.items()
        }

        # Overall quality score
        if domain_scores:
            quality_score = sum(domain_scores.values()) / len(domain_scores)
        else:
            quality_score = 0.0

        # Success factor
        success_count = sum(1 for o in outcomes if o.success)
        success_rate = success_count / len(outcomes)

        # Weighted quality
        weighted_quality = quality_score * 0.7 + (success_rate * 2 - 1) * 0.3

        # Confidence based on number of outcomes
        confidence = min(len(outcomes) / 3.0, 1.0)

        return {
            "quality_score": weighted_quality,
            "confidence": confidence,
            "success_rate": success_rate,
            "domain_scores": domain_scores,
            "total_outcomes": len(outcomes),
            "reasoning": f"Based on {len(outcomes)} outcomes across {len(domain_scores)} domains",
        }

    def get_all_outcomes(self) -> List[OutcomeRecord]:
        """Get all outcome records.

        Returns:
            List of all outcome records
        """
        all_outcomes: List[OutcomeRecord] = []
        for outcomes in self.outcomes.values():
            all_outcomes.extend(outcomes)
        return all_outcomes

    def clear(self) -> None:
        """Clear all tracked outcomes and reset metrics."""
        self.outcomes.clear()
        self.pending_outcomes.clear()
        self.causal_chains.clear()
        self.metrics = {
            "total_outcomes": 0,
            "immediate_outcomes": 0,
            "short_term_outcomes": 0,
            "long_term_outcomes": 0,
            "avg_reward_signal": 0.0,
            "correlation_time_ms": 0.0,
        }
        logger.info("OutcomeTracker cleared")
