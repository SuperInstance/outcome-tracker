"""
Aggregators for outcome data.

This module provides various aggregation strategies for analyzing outcome data
across different dimensions: time windows, domains, and characters.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from outcome_tracker.core import (
    OutcomeRecord,
    RewardDomain,
    OutcomeType,
    OutcomeTracker,
)

logger = logging.getLogger(__name__)


@dataclass
class TimeWindow:
    """A time window for aggregation.

    Attributes:
        start: Start timestamp (unix timestamp)
        end: End timestamp (unix timestamp)
        label: Optional label for this window
    """
    start: float
    end: float
    label: Optional[str] = None

    def contains(self, timestamp: float) -> bool:
        """Check if a timestamp falls within this window.

        Args:
            timestamp: Unix timestamp to check

        Returns:
            True if timestamp is within the window
        """
        return self.start <= timestamp <= self.end


@dataclass
class AggregationResult:
    """Result of an aggregation operation.

    Attributes:
        key: The aggregation key (e.g., domain name, time window label)
        count: Number of outcomes in this aggregation
        success_count: Number of successful outcomes
        total_reward: Sum of all reward values
        avg_reward: Average reward value
        domain_breakdown: Reward breakdown by domain
        metadata: Additional metadata about the aggregation
    """
    key: str
    count: int
    success_count: int
    total_reward: float
    avg_reward: float
    domain_breakdown: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.success_count / self.count if self.count > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "count": self.count,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "total_reward": self.total_reward,
            "avg_reward": self.avg_reward,
            "domain_breakdown": self.domain_breakdown,
            "metadata": self.metadata,
        }


class TimeWindowAggregator:
    """Aggregates outcomes within time windows.

    Useful for analyzing trends over time, such as:
    - Hourly performance
    - Daily summaries
    - Session-based analysis

    Example:
        >>> aggregator = TimeWindowAggregator(tracker)
        >>> # Get last hour's outcomes
        >>> results = aggregator.aggregate_by_window(
        ...     windows=[TimeWindow(start=time.time()-3600, end=time.time())]
        ... )
    """

    def __init__(self, tracker: OutcomeTracker) -> None:
        """Initialize with an OutcomeTracker instance.

        Args:
            tracker: The OutcomeTracker to aggregate from
        """
        self.tracker = tracker

    def aggregate_by_window(
        self,
        windows: List[TimeWindow],
    ) -> List[AggregationResult]:
        """Aggregate outcomes within specified time windows.

        Args:
            windows: List of time windows to aggregate

        Returns:
            List of aggregation results, one per window
        """
        all_outcomes = self.tracker.get_all_outcomes()

        results: List[AggregationResult] = []

        for window in windows:
            window_outcomes = [
                o for o in all_outcomes
                if window.contains(o.timestamp)
            ]

            result = self._aggregate_outcomes(
                outcomes=window_outcomes,
                key=window.label or f"{window.start}-{window.end}",
            )
            result.metadata["window_start"] = window.start
            result.metadata["window_end"] = window.end

            results.append(result)

        return results

    def aggregate_by_interval(
        self,
        interval_seconds: float,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[AggregationResult]:
        """Aggregate outcomes by regular time intervals.

        Args:
            interval_seconds: Length of each interval in seconds
            start_time: Start time (defaults to earliest outcome)
            end_time: End time (defaults to latest outcome)

        Returns:
            List of aggregation results, one per interval
        """
        all_outcomes = self.tracker.get_all_outcomes()

        if not all_outcomes:
            return []

        # Determine time range
        if start_time is None:
            start_time = min(o.timestamp for o in all_outcomes)
        if end_time is None:
            end_time = max(o.timestamp for o in all_outcomes)

        # Create windows
        windows: List[TimeWindow] = []
        current_start = start_time

        while current_start < end_time:
            current_end = min(current_start + interval_seconds, end_time)
            window_label = datetime.fromtimestamp(current_start).strftime("%Y-%m-%d %H:%M")
            windows.append(TimeWindow(current_start, current_end, window_label))
            current_start = current_end

        return self.aggregate_by_window(windows)

    def aggregate_last_n_minutes(self, minutes: int) -> AggregationResult:
        """Aggregate outcomes from the last N minutes.

        Args:
            minutes: Number of minutes to look back

        Returns:
            Aggregation result for the time period
        """
        import time
        cutoff = time.time() - (minutes * 60)

        recent_outcomes = [
            o for o in self.tracker.get_all_outcomes()
            if o.timestamp >= cutoff
        ]

        return self._aggregate_outcomes(
            outcomes=recent_outcomes,
            key=f"last_{minutes}_min",
        )

    def _aggregate_outcomes(
        self,
        outcomes: List[OutcomeRecord],
        key: str,
    ) -> AggregationResult:
        """Aggregate a list of outcomes into a result.

        Args:
            outcomes: List of outcomes to aggregate
            key: Key for the result

        Returns:
            AggregationResult
        """
        if not outcomes:
            return AggregationResult(
                key=key,
                count=0,
                success_count=0,
                total_reward=0.0,
                avg_reward=0.0,
            )

        success_count = sum(1 for o in outcomes if o.success)

        # Calculate rewards
        all_rewards: List[float] = []
        domain_rewards: Dict[str, List[float]] = {}

        for outcome in outcomes:
            for reward in outcome.rewards:
                all_rewards.append(reward.value * reward.confidence)

                domain = reward.domain.value
                if domain not in domain_rewards:
                    domain_rewards[domain] = []
                domain_rewards[domain].append(reward.value * reward.confidence)

        total_reward = sum(all_rewards)
        avg_reward = total_reward / len(all_rewards) if all_rewards else 0.0

        # Domain breakdown
        domain_breakdown = {
            domain: sum(rewards) / len(rewards)
            for domain, rewards in domain_rewards.items()
        }

        return AggregationResult(
            key=key,
            count=len(outcomes),
            success_count=success_count,
            total_reward=total_reward,
            avg_reward=avg_reward,
            domain_breakdown=domain_breakdown,
        )


class DomainAggregator:
    """Aggregates outcomes by reward domain.

    Useful for understanding performance across different activity types:
    - How well is the agent doing in combat?
    - Are social interactions improving?
    - Is exploration yielding results?

    Example:
        >>> aggregator = DomainAggregator(tracker)
        >>> results = aggregator.aggregate_by_domain()
        >>> combat_result = results[RewardDomain.COMBAT]
        >>> print(f"Combat success rate: {combat_result.success_rate:.1%}")
    """

    def __init__(self, tracker: OutcomeTracker) -> None:
        """Initialize with an OutcomeTracker instance.

        Args:
            tracker: The OutcomeTracker to aggregate from
        """
        self.tracker = tracker

    def aggregate_by_domain(self) -> Dict[RewardDomain, AggregationResult]:
        """Aggregate outcomes by reward domain.

        Returns:
            Dictionary mapping domains to aggregation results
        """
        all_outcomes = self.tracker.get_all_outcomes()
        results: Dict[RewardDomain, List[OutcomeRecord]] = {}

        # Group outcomes by their primary domain
        for outcome in all_outcomes:
            if outcome.rewards:
                # Use the highest-confidence reward as the primary domain
                primary_reward = max(outcome.rewards, key=lambda r: r.confidence)
                domain = primary_reward.domain

                if domain not in results:
                    results[domain] = []
                results[domain].append(outcome)

        # Calculate aggregations
        aggregations: Dict[RewardDomain, AggregationResult] = {}

        for domain, outcomes in results.items():
            rewards: List[float] = []
            for outcome in outcomes:
                for reward in outcome.rewards:
                    if reward.domain == domain:
                        rewards.append(reward.value * reward.confidence)

            total_reward = sum(rewards)
            avg_reward = total_reward / len(rewards) if rewards else 0.0
            success_count = sum(1 for o in outcomes if o.success)

            aggregations[domain] = AggregationResult(
                key=domain.value,
                count=len(outcomes),
                success_count=success_count,
                total_reward=total_reward,
                avg_reward=avg_reward,
                domain_breakdown={domain.value: avg_reward},
            )

        return aggregations

    def get_domain_summary(self) -> Dict[str, Any]:
        """Get a summary of performance across all domains.

        Returns:
            Dictionary with domain-wise statistics
        """
        aggregations = self.aggregate_by_domain()

        return {
            domain.value: {
                "count": agg.count,
                "success_rate": agg.success_rate,
                "avg_reward": agg.avg_reward,
                "total_reward": agg.total_reward,
            }
            for domain, agg in aggregations.items()
        }

    def get_best_domain(self) -> Optional[RewardDomain]:
        """Get the domain with the highest average reward.

        Returns:
            The best performing domain, or None if no data
        """
        aggregations = self.aggregate_by_domain()

        if not aggregations:
            return None

        return max(aggregations.items(), key=lambda x: x[1].avg_reward)[0]

    def get_worst_domain(self) -> Optional[RewardDomain]:
        """Get the domain with the lowest average reward.

        Returns:
            The worst performing domain, or None if no data
        """
        aggregations = self.aggregate_by_domain()

        if not aggregations:
            return None

        return min(aggregations.items(), key=lambda x: x[1].avg_reward)[0]


class CharacterAggregator:
    """Aggregates outcomes by character/agent.

    Useful for multi-agent systems or tracking individual character performance.

    Example:
        >>> aggregator = CharacterAggregator(tracker)
        >>> results = aggregator.aggregate_by_character()
        >>> for character_id, result in results.items():
        ...     print(f"{character_id}: {result.success_rate:.1%} success")
    """

    def __init__(self, tracker: OutcomeTracker) -> None:
        """Initialize with an OutcomeTracker instance.

        Args:
            tracker: The OutcomeTracker to aggregate from
        """
        self.tracker = tracker

    def aggregate_by_character(self) -> Dict[str, AggregationResult]:
        """Aggregate outcomes by character ID.

        Character ID is extracted from the context metadata
        (context["character_id"]).

        Returns:
            Dictionary mapping character IDs to aggregation results
        """
        all_outcomes = self.tracker.get_all_outcomes()
        character_outcomes: Dict[str, List[OutcomeRecord]] = {}

        for outcome in all_outcomes:
            character_id = outcome.metadata.get("context", {}).get("character_id", "unknown")

            if character_id not in character_outcomes:
                character_outcomes[character_id] = []
            character_outcomes[character_id].append(outcome)

        # Calculate aggregations
        results: Dict[str, AggregationResult] = {}

        for character_id, outcomes in character_outcomes.items():
            rewards: List[float] = []
            domain_rewards: Dict[str, List[float]] = {}

            for outcome in outcomes:
                for reward in outcome.rewards:
                    rewards.append(reward.value * reward.confidence)

                    domain = reward.domain.value
                    if domain not in domain_rewards:
                        domain_rewards[domain] = []
                    domain_rewards[domain].append(reward.value * reward.confidence)

            total_reward = sum(rewards)
            avg_reward = total_reward / len(rewards) if rewards else 0.0
            success_count = sum(1 for o in outcomes if o.success)

            # Domain breakdown
            domain_breakdown = {
                domain: sum(vals) / len(vals)
                for domain, vals in domain_rewards.items()
            }

            results[character_id] = AggregationResult(
                key=character_id,
                count=len(outcomes),
                success_count=success_count,
                total_reward=total_reward,
                avg_reward=avg_reward,
                domain_breakdown=domain_breakdown,
            )

        return results

    def get_character_ranking(self) -> List[tuple[str, float]]:
        """Get characters ranked by average reward.

        Returns:
            List of (character_id, avg_reward) tuples, sorted by reward descending
        """
        aggregations = self.aggregate_by_character()

        ranked = [
            (char_id, agg.avg_reward)
            for char_id, agg in aggregations.items()
        ]

        return sorted(ranked, key=lambda x: x[1], reverse=True)

    def get_top_character(self, n: int = 1) -> List[tuple[str, float]]:
        """Get the top N characters by average reward.

        Args:
            n: Number of top characters to return

        Returns:
            List of (character_id, avg_reward) tuples
        """
        ranking = self.get_character_ranking()
        return ranking[:n]


class CustomAggregator:
    """Aggregates outcomes using a custom key function.

    This allows flexible aggregation based on any criteria:
    - By decision type
    - By success/failure
    - By outcome type
    - Custom combinations

    Example:
        >>> aggregator = CustomAggregator(tracker)
        >>> # Aggregate by outcome type
        >>> results = aggregator.aggregate(
        ...     key_fn=lambda o: o.outcome_type.value
        ... )
        >>> print(results["immediate"].success_rate)
    """

    def __init__(self, tracker: OutcomeTracker) -> None:
        """Initialize with an OutcomeTracker instance.

        Args:
            tracker: The OutcomeTracker to aggregate from
        """
        self.tracker = tracker

    def aggregate(
        self,
        key_fn: Callable[[OutcomeRecord], str],
        filter_fn: Optional[Callable[[OutcomeRecord], bool]] = None,
    ) -> Dict[str, AggregationResult]:
        """Aggregate outcomes using a custom key function.

        Args:
            key_fn: Function that extracts a key from each outcome
            filter_fn: Optional function to filter outcomes

        Returns:
            Dictionary mapping keys to aggregation results
        """
        all_outcomes = self.tracker.get_all_outcomes()

        if filter_fn:
            all_outcomes = [o for o in all_outcomes if filter_fn(o)]

        grouped: Dict[str, List[OutcomeRecord]] = {}

        for outcome in all_outcomes:
            key = key_fn(outcome)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(outcome)

        results: Dict[str, AggregationResult] = {}

        for key, outcomes in grouped.items():
            rewards: List[float] = []
            domain_rewards: Dict[str, List[float]] = {}

            for outcome in outcomes:
                for reward in outcome.rewards:
                    rewards.append(reward.value * reward.confidence)

                    domain = reward.domain.value
                    if domain not in domain_rewards:
                        domain_rewards[domain] = []
                    domain_rewards[domain].append(reward.value * reward.confidence)

            total_reward = sum(rewards)
            avg_reward = total_reward / len(rewards) if rewards else 0.0
            success_count = sum(1 for o in outcomes if o.success)

            domain_breakdown = {
                domain: sum(vals) / len(vals)
                for domain, vals in domain_rewards.items()
            }

            results[key] = AggregationResult(
                key=key,
                count=len(outcomes),
                success_count=success_count,
                total_reward=total_reward,
                avg_reward=avg_reward,
                domain_breakdown=domain_breakdown,
            )

        return results
