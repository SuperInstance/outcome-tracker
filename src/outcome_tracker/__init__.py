"""
Outcome Tracker - A sophisticated multi-domain reward tracking system for AI agents.

This package provides tools for tracking decision outcomes across multiple domains:
- Combat outcomes (damage, tactical advantage, enemy defeats)
- Social outcomes (relationship changes, persuasion, trust)
- Exploration outcomes (discovery, progress, secrets)
- Resource outcomes (XP, gold, items)
- Strategic outcomes (positioning, opportunities, goals)

Example:
    >>> from outcome_tracker import OutcomeTracker, RewardDomain
    >>>
    >>> tracker = OutcomeTracker()
    >>>
    >>> # Track an immediate outcome
    >>> outcome = tracker.track_immediate_outcome(
    ...     decision_id="combat_001",
    ...     description="Hit goblin for 15 damage, goblin defeated",
    ...     success=True,
    ...     context={"decision_type": "combat_action", "character_id": "thorin"}
    ... )
    >>>
    >>> # Get aggregate reward
    >>> reward = tracker.get_aggregate_reward("combat_001", RewardDomain.COMBAT)
    >>>
    >>> # Export to JSON
    >>> tracker.export_json("outcomes.json")
"""

from outcome_tracker.core import (
    OutcomeTracker,
    OutcomeRecord,
    RewardSignal,
    RewardDomain,
    OutcomeType,
)

from outcome_tracker.aggregators import (
    TimeWindowAggregator,
    DomainAggregator,
    CharacterAggregator,
)

from outcome_tracker.exporters import (
    JSONExporter,
    CSVExporter,
    ExportFormat,
)

__version__ = "1.0.0"
__all__ = [
    # Core classes
    "OutcomeTracker",
    "OutcomeRecord",
    "RewardSignal",
    "RewardDomain",
    "OutcomeType",
    # Aggregators
    "TimeWindowAggregator",
    "DomainAggregator",
    "CharacterAggregator",
    # Exporters
    "JSONExporter",
    "CSVExporter",
    "ExportFormat",
]
