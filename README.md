# Outcome Tracker

A sophisticated multi-domain reward tracking system for AI agents and reinforcement learning applications.

## Features

- **Multi-Domain Reward Tracking**: Track outcomes across combat, social, exploration, resource, and strategic domains
- **Temporal Correlation**: Support for immediate, short-term, and long-term outcomes
- **Causal Chain Tracking**: Trace how decisions lead to outcomes over time
- **Flexible Aggregation**: Analyze outcomes by time windows, domains, characters, or custom criteria
- **Multiple Export Formats**: Export to JSON, CSV, or use the pretty-printed summaries
- **Decision Quality Analysis**: Automated analysis of decision quality based on outcomes

## Installation

```bash
pip install outcome-tracker
```

Or install from source:

```bash
git clone https://github.com/casey/outcome-tracker
cd outcome-tracker
pip install -e .
```

## Quick Start

```python
from outcome_tracker import OutcomeTracker, RewardDomain

# Initialize the tracker
tracker = OutcomeTracker()

# Track an immediate outcome
outcome = tracker.track_immediate_outcome(
    decision_id="combat_001",
    description="Hit goblin for 15 damage, goblin defeated",
    success=True,
    context={
        "decision_type": "combat_action",
        "character_id": "thorin",
    }
)

# Get aggregate reward
reward = tracker.get_aggregate_reward("combat_001", RewardDomain.COMBAT)
print(f"Combat reward: {reward:.3f}")

# Analyze decision quality
quality = tracker.analyze_decision_quality("combat_001")
print(f"Quality score: {quality['quality_score']:.3f}")
```

## Core Concepts

### Outcome Types

Outcomes are classified by their temporal relationship to decisions:

- **Immediate**: Happens right after the decision (hit/miss, accept/reject)
- **Short-term**: Occurs within the same encounter (5-10 turns later)
- **Long-term**: Manifests across multiple encounters (session-wide)

### Reward Domains

Rewards are calculated across multiple domains:

- **Combat**: Damage dealt, enemies defeated, tactical advantage
- **Social**: Relationship changes, persuasion success, trust building
- **Exploration**: Discoveries, secrets revealed, map knowledge
- **Resource**: XP gained, gold acquired, items found
- **Strategic**: Positioning, opportunities created, goal progress

## Usage Examples

### Tracking Outcomes

```python
from outcome_tracker import OutcomeTracker, OutcomeType

tracker = OutcomeTracker()

# Immediate outcome
tracker.track_immediate_outcome(
    decision_id="social_001",
    description="Convinced merchant, relationship improved +5",
    success=True,
    context={"decision_type": "social", "character_id": "elara"}
)

# Delayed outcome with causal chain
tracker.track_delayed_outcome(
    decision_id="combat_001",
    description="Party safe, gained 50 XP",
    success=True,
    context={"decision_type": "combat_action"},
    outcome_type=OutcomeType.SHORT_TERM,
    related_decisions=["combat_001", "combat_002"]
)
```

### Aggregation

```python
from outcome_tracker.aggregators import DomainAggregator, TimeWindowAggregator

# Aggregate by domain
domain_agg = DomainAggregator(tracker)
results = domain_agg.aggregate_by_domain()

for domain, result in results.items():
    print(f"{domain.value}: {result.success_rate:.1%} success")

# Time-based aggregation
time_agg = TimeWindowAggregator(tracker)
recent = time_agg.aggregate_last_n_minutes(60)
print(f"Last hour: {recent.count} outcomes")
```

### Export

```python
from outcome_tracker.exporters import JSONExporter, CSVExporter

# Export to JSON
json_exporter = JSONExporter(tracker)
json_exporter.export("outcomes.json", indent=2)

# Export to CSV
csv_exporter = CSVExporter(tracker)
csv_exporter.export("outcomes.csv")

# Or use the convenience function
from outcome_tracker.exporters import export_outcomes
export_outcomes(tracker, "outcomes.json", format="json")
```

## API Reference

### OutcomeTracker

Main class for tracking decision outcomes.

#### Methods

- `track_immediate_outcome(decision_id, description, success, context)` - Track an immediate outcome
- `track_delayed_outcome(decision_id, description, success, context, outcome_type, related_decisions)` - Track a delayed outcome
- `get_aggregate_reward(decision_id, domain=None)` - Get aggregate reward for a decision
- `get_success_rate(decision_type=None)` - Get overall success rate
- `get_statistics()` - Get tracking statistics
- `analyze_decision_quality(decision_id)` - Analyze decision quality
- `get_outcomes_for_decision(decision_id)` - Get all outcomes for a decision
- `clear()` - Clear all tracked outcomes

### Aggregators

#### DomainAggregator
- `aggregate_by_domain()` - Aggregate outcomes by reward domain
- `get_domain_summary()` - Get summary statistics by domain
- `get_best_domain()` - Get best performing domain
- `get_worst_domain()` - Get worst performing domain

#### TimeWindowAggregator
- `aggregate_by_window(windows)` - Aggregate within time windows
- `aggregate_by_interval(interval_seconds)` - Aggregate by regular intervals
- `aggregate_last_n_minutes(minutes)` - Aggregate recent outcomes

#### CharacterAggregator
- `aggregate_by_character()` - Aggregate by character ID
- `get_character_ranking()` - Get characters ranked by performance
- `get_top_character(n)` - Get top N characters

#### CustomAggregator
- `aggregate(key_fn, filter_fn=None)` - Aggregate using custom criteria

### Exporters

#### JSONExporter
- `export(filepath, indent=None)` - Export to JSON file
- `export_to_string()` - Export to JSON string
- `export_by_decision(filepath, decision_id)` - Export specific decision
- `export_by_domain(filepath, domain)` - Export filtered by domain

#### CSVExporter
- `export(filepath, columns=None, flatten_rewards=False)` - Export to CSV
- `export_by_decision(filepath, decision_id)` - Export specific decision
- `export_summary(filepath)` - Export summary statistics

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Running Examples

```bash
# Basic usage
python examples/basic_usage.py

# Aggregation
python examples/aggregation_example.py

# Export
python examples/export_example.py

# RL integration
python examples/rl_integration_example.py
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
