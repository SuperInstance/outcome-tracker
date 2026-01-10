"""
Exporters for outcome data.

This module provides functionality to export outcome data to various formats
including JSON, CSV, and custom formats.
"""

import json
import csv
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from enum import Enum
from dataclasses import asdict

from outcome_tracker.core import (
    OutcomeTracker,
    OutcomeRecord,
    RewardDomain,
    OutcomeType,
)

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    PRETTY = "pretty"


class JSONExporter:
    """Exports outcome data to JSON format.

    Example:
        >>> exporter = JSONExporter(tracker)
        >>> exporter.export("outcomes.json")
        >>> # Or with options
        >>> exporter.export("outcomes.json", indent=2, include_metadata=True)
    """

    def __init__(self, tracker: OutcomeTracker) -> None:
        """Initialize with an OutcomeTracker instance.

        Args:
            tracker: The OutcomeTracker to export from
        """
        self.tracker = tracker

    def export(
        self,
        filepath: Union[str, Path],
        indent: Optional[int] = None,
        include_metadata: bool = True,
    ) -> None:
        """Export all outcomes to a JSON file.

        Args:
            filepath: Path to the output file
            indent: JSON indentation (None for compact)
            include_metadata: Whether to include metadata
        """
        data = self._prepare_data(include_metadata)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=indent, default=self._json_serializer)

        logger.info(f"Exported {len(data['outcomes'])} outcomes to {filepath}")

    def export_to_string(
        self,
        indent: Optional[int] = None,
        include_metadata: bool = True,
    ) -> str:
        """Export outcomes to a JSON string.

        Args:
            indent: JSON indentation (None for compact)
            include_metadata: Whether to include metadata

        Returns:
            JSON string
        """
        data = self._prepare_data(include_metadata)
        return json.dumps(data, indent=indent, default=self._json_serializer)

    def export_by_decision(
        self,
        filepath: Union[str, Path],
        decision_id: str,
    ) -> None:
        """Export outcomes for a specific decision.

        Args:
            filepath: Path to the output file
            decision_id: Decision ID to export
        """
        outcomes = self.tracker.get_outcomes_for_decision(decision_id)

        data = {
            "decision_id": decision_id,
            "outcomes": [o.to_dict() for o in outcomes],
            "aggregate_reward": self.tracker.get_aggregate_reward(decision_id),
            "quality_analysis": self.tracker.analyze_decision_quality(decision_id),
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=self._json_serializer)

        logger.info(f"Exported {len(outcomes)} outcomes for decision {decision_id} to {filepath}")

    def export_by_domain(
        self,
        filepath: Union[str, Path],
        domain: RewardDomain,
    ) -> None:
        """Export outcomes filtered by domain.

        Args:
            filepath: Path to the output file
            domain: Domain to filter by
        """
        all_outcomes = self.tracker.get_all_outcomes()

        filtered = [
            o for o in all_outcomes
            if any(r.domain == domain for r in o.rewards)
        ]

        data = {
            "domain": domain.value,
            "outcomes": [o.to_dict() for o in filtered],
            "count": len(filtered),
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=self._json_serializer)

        logger.info(f"Exported {len(filtered)} outcomes for domain {domain.value} to {filepath}")

    def _prepare_data(self, include_metadata: bool) -> Dict[str, Any]:
        """Prepare data for export.

        Args:
            include_metadata: Whether to include metadata

        Returns:
            Dictionary with all outcome data
        """
        outcomes = self.tracker.get_all_outcomes()

        data: Dict[str, Any] = {
            "outcomes": [o.to_dict() for o in outcomes],
            "statistics": self.tracker.get_statistics(),
        }

        if include_metadata:
            data["metrics"] = self.tracker.metrics

        return data

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Custom JSON serializer for non-serializable objects.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation
        """
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "value"):
            return obj.value
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class CSVExporter:
    """Exports outcome data to CSV format.

    Example:
        >>> exporter = CSVExporter(tracker)
        >>> exporter.export("outcomes.csv")
        >>> # Or specify columns
        >>> exporter.export("outcomes.csv", columns=["decision_id", "success", "timestamp"])
    """

    # Default columns for export
    DEFAULT_COLUMNS = [
        "decision_id",
        "outcome_type",
        "timestamp",
        "description",
        "success",
        "reward_domains",
        "total_reward",
        "avg_reward",
    ]

    def __init__(self, tracker: OutcomeTracker) -> None:
        """Initialize with an OutcomeTracker instance.

        Args:
            tracker: The OutcomeTracker to export from
        """
        self.tracker = tracker

    def export(
        self,
        filepath: Union[str, Path],
        columns: Optional[List[str]] = None,
        flatten_rewards: bool = False,
    ) -> None:
        """Export all outcomes to a CSV file.

        Args:
            filepath: Path to the output file
            columns: Columns to include (None for default)
            flatten_rewards: Whether to create separate columns for each domain
        """
        outcomes = self.tracker.get_all_outcomes()

        if columns is None:
            columns = list(self.DEFAULT_COLUMNS)
            if flatten_rewards:
                for domain in RewardDomain:
                    columns.append(f"{domain.value}_reward")

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()

            for outcome in outcomes:
                row = self._outcome_to_row(
                    outcome,
                    flatten_rewards=flatten_rewards,
                )
                writer.writerow(row)

        logger.info(f"Exported {len(outcomes)} outcomes to {filepath}")

    def export_by_decision(
        self,
        filepath: Union[str, Path],
        decision_id: str,
    ) -> None:
        """Export outcomes for a specific decision.

        Args:
            filepath: Path to the output file
            decision_id: Decision ID to export
        """
        outcomes = self.tracker.get_outcomes_for_decision(decision_id)

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self.DEFAULT_COLUMNS,
                extrasaction="ignore",
            )
            writer.writeheader()

            for outcome in outcomes:
                row = self._outcome_to_row(outcome)
                writer.writerow(row)

        logger.info(f"Exported {len(outcomes)} outcomes for decision {decision_id} to {filepath}")

    def export_summary(
        self,
        filepath: Union[str, Path],
    ) -> None:
        """Export a summary of outcomes to CSV.

        Creates a summary with one row per decision, including aggregate stats.

        Args:
            filepath: Path to the output file
        """
        columns = [
            "decision_id",
            "outcome_count",
            "success_count",
            "success_rate",
            "total_reward",
            "avg_reward",
            "domains",
        ]

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()

            for decision_id in self.tracker.outcomes.keys():
                outcomes = self.tracker.get_outcomes_for_decision(decision_id)

                # Get unique domains
                domains = set()
                for o in outcomes:
                    for r in o.rewards:
                        domains.add(r.domain.value)

                # Calculate rewards
                all_rewards = [
                    r.value * r.confidence
                    for o in outcomes
                    for r in o.rewards
                ]

                row = {
                    "decision_id": decision_id,
                    "outcome_count": len(outcomes),
                    "success_count": sum(1 for o in outcomes if o.success),
                    "success_rate": sum(1 for o in outcomes if o.success) / len(outcomes) if outcomes else 0,
                    "total_reward": sum(all_rewards),
                    "avg_reward": sum(all_rewards) / len(all_rewards) if all_rewards else 0,
                    "domains": ",".join(sorted(domains)),
                }

                writer.writerow(row)

        logger.info(f"Exported summary to {filepath}")

    def _outcome_to_row(
        self,
        outcome: OutcomeRecord,
        flatten_rewards: bool = False,
    ) -> Dict[str, Any]:
        """Convert an outcome to a CSV row.

        Args:
            outcome: The outcome record
            flatten_rewards: Whether to flatten reward domains

        Returns:
            Dictionary representing the row
        """
        row: Dict[str, Any] = {
            "decision_id": outcome.decision_id,
            "outcome_type": outcome.outcome_type.value,
            "timestamp": outcome.timestamp,
            "description": outcome.description,
            "success": outcome.success,
        }

        if outcome.rewards:
            domains = [r.domain.value for r in outcome.rewards]
            row["reward_domains"] = ",".join(set(domains))

            rewards = [r.value * r.confidence for r in outcome.rewards]
            row["total_reward"] = sum(rewards)
            row["avg_reward"] = sum(rewards) / len(rewards)

            if flatten_rewards:
                for reward in outcome.rewards:
                    key = f"{reward.domain.value}_reward"
                    row[key] = reward.value * reward.confidence
        else:
            row["reward_domains"] = ""
            row["total_reward"] = 0
            row["avg_reward"] = 0

        return row


class PrettyPrinter:
    """Prints outcome data in a human-readable format.

    Example:
        >>> printer = PrettyPrinter(tracker)
        >>> printer.print_summary()
        >>> printer.print_decision_outcomes("combat_001")
    """

    def __init__(self, tracker: OutcomeTracker) -> None:
        """Initialize with an OutcomeTracker instance.

        Args:
            tracker: The OutcomeTracker to print from
        """
        self.tracker = tracker

    def print_summary(self) -> None:
        """Print a summary of all outcomes."""
        stats = self.tracker.get_statistics()

        print("=" * 60)
        print("OUTCOME TRACKER SUMMARY")
        print("=" * 60)

        print(f"\nTotal Outcomes: {stats['total_outcomes']}")
        print(f"Overall Success Rate: {stats['success_rate_overall']:.1%}")

        print("\nOutcome Types:")
        print(f"  Immediate: {stats['immediate_outcomes']} ({stats.get('immediate_pct', 0):.1%})")
        print(f"  Short-term: {stats['short_term_outcomes']} ({stats.get('short_term_pct', 0):.1%})")
        print(f"  Long-term: {stats['long_term_outcomes']} ({stats.get('long_term_pct', 0):.1%})")

        print("\nSuccess Rates by Type:")
        print(f"  Combat: {stats['success_rate_combat']:.1%}")
        print(f"  Social: {stats['success_rate_social']:.1%}")
        print(f"  Exploration: {stats['success_rate_exploration']:.1%}")

        print(f"\nAverage Reward Signal: {stats['avg_reward_signal']:.3f}")
        print(f"Avg Correlation Time: {stats['correlation_time_ms']:.2f}ms")

        if stats.get("total_causal_chains", 0) > 0:
            print(f"\nCausal Chains: {stats['total_causal_chains']}")
            print(f"Avg Chain Length: {stats.get('avg_chain_length', 0):.1f}")

        print("\n" + "=" * 60)

    def print_decision_outcomes(self, decision_id: str) -> None:
        """Print outcomes for a specific decision.

        Args:
            decision_id: Decision ID to print
        """
        outcomes = self.tracker.get_outcomes_for_decision(decision_id)

        if not outcomes:
            print(f"No outcomes found for decision: {decision_id}")
            return

        quality = self.tracker.analyze_decision_quality(decision_id)

        print("=" * 60)
        print(f"DECISION: {decision_id}")
        print("=" * 60)

        print(f"\nQuality Score: {quality['quality_score']:.3f} (confidence: {quality['confidence']:.2f})")
        print(f"Success Rate: {quality['success_rate']:.1%}")
        print(f"Total Outcomes: {quality['total_outcomes']}")

        if quality.get('domain_scores'):
            print("\nDomain Scores:")
            for domain, score in quality['domain_scores'].items():
                print(f"  {domain}: {score:.3f}")

        print("\nOutcomes:")
        for i, outcome in enumerate(outcomes, 1):
            status = "SUCCESS" if outcome.success else "FAILURE"
            print(f"\n  [{i}] {outcome.outcome_type.value.upper()} - {status}")
            print(f"      {outcome.description}")

            if outcome.rewards:
                print(f"      Rewards:")
                for reward in outcome.rewards:
                    print(f"        {reward.domain.value}: {reward.value:.3f} (conf: {reward.confidence:.2f})")

        print("\n" + "=" * 60)

    def print_domain_summary(self) -> None:
        """Print a summary by reward domain."""
        from outcome_tracker.aggregators import DomainAggregator

        aggregator = DomainAggregator(self.tracker)
        summary = aggregator.get_domain_summary()

        print("=" * 60)
        print("DOMAIN SUMMARY")
        print("=" * 60)

        for domain, stats in summary.items():
            print(f"\n{domain.upper()}:")
            print(f"  Count: {stats['count']}")
            print(f"  Success Rate: {stats['success_rate']:.1%}")
            print(f"  Avg Reward: {stats['avg_reward']:.3f}")
            print(f"  Total Reward: {stats['total_reward']:.3f}")

        print("\n" + "=" * 60)


def export_outcomes(
    tracker: OutcomeTracker,
    filepath: Union[str, Path],
    format: Union[str, ExportFormat] = ExportFormat.JSON,
    **kwargs: Any,
) -> None:
    """Convenience function to export outcomes in any format.

    Args:
        tracker: The OutcomeTracker to export from
        filepath: Path to the output file
        format: Export format (json or csv)
        **kwargs: Additional arguments passed to the exporter

    Example:
        >>> export_outcomes(tracker, "outcomes.json", format="json")
        >>> export_outcomes(tracker, "outcomes.csv", format="csv", flatten_rewards=True)
    """
    if isinstance(format, str):
        format = ExportFormat(format.lower())

    filepath = Path(filepath)

    if format == ExportFormat.JSON:
        exporter = JSONExporter(tracker)
        exporter.export(filepath, **kwargs)
    elif format == ExportFormat.CSV:
        exporter = CSVExporter(tracker)
        exporter.export(filepath, **kwargs)
    else:
        raise ValueError(f"Unsupported export format: {format}")
