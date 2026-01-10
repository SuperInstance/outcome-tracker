"""
Aggregation Example for Outcome Tracker

This example demonstrates how to use the aggregators to analyze
outcomes across different dimensions: time, domain, and character.
"""

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
)


def setup_tracker():
    """Create a tracker with sample data."""
    tracker = OutcomeTracker()

    # Thorin's combat actions
    tracker.track_immediate_outcome(
        decision_id="thorin_combat_1",
        description="Hit goblin for 12 damage",
        success=True,
        context={"decision_type": "combat_action", "character_id": "thorin"},
    )
    tracker.track_immediate_outcome(
        decision_id="thorin_combat_2",
        description="Missed attack on orc",
        success=False,
        context={"decision_type": "combat_action", "character_id": "thorin"},
    )
    tracker.track_immediate_outcome(
        decision_id="thorin_combat_3",
        description="Defeated enemy with critical hit",
        success=True,
        context={"decision_type": "combat_action", "character_id": "thorin"},
    )

    # Elara's social interactions
    tracker.track_immediate_outcome(
        decision_id="elara_social_1",
        description="Persuaded guard to let us pass",
        success=True,
        context={"decision_type": "social", "character_id": "elara"},
    )
    tracker.track_immediate_outcome(
        decision_id="elara_social_2",
        description="Failed to convince merchant",
        success=False,
        context={"decision_type": "social", "character_id": "elara"},
    )

    # Shared exploration
    tracker.track_immediate_outcome(
        decision_id="explore_shared",
        description="Discovered ancient ruins",
        success=True,
        context={"decision_type": "exploration", "character_id": "thorin"},
    )

    # Resource gains
    tracker.track_delayed_outcome(
        decision_id="thorin_combat_3",
        description="Looted 100 gold and 75 XP",
        success=True,
        context={"decision_type": "combat_action"},
        outcome_type=OutcomeType.SHORT_TERM,
    )

    return tracker


def main():
    """Run the aggregation example."""
    print("=" * 60)
    print("Outcome Tracker - Aggregation Example")
    print("=" * 60)

    tracker = setup_tracker()

    # Example 1: Domain aggregation
    print("\n[Example 1] Aggregating by domain...")
    domain_agg = DomainAggregator(tracker)
    domain_results = domain_agg.aggregate_by_domain()

    for domain, result in domain_results.items():
        print(f"\n  {domain.value.upper()}:")
        print(f"    Count: {result.count}")
        print(f"    Success rate: {result.success_rate:.1%}")
        print(f"    Avg reward: {result.avg_reward:.3f}")

    # Example 2: Best and worst domains
    print("\n[Example 2] Finding best/worst domains...")
    best = domain_agg.get_best_domain()
    worst = domain_agg.get_worst_domain()
    print(f"  - Best domain: {best.value if best else 'None'}")
    print(f"  - Worst domain: {worst.value if worst else 'None'}")

    # Example 3: Domain summary
    print("\n[Example 3] Domain summary...")
    summary = domain_agg.get_domain_summary()
    for domain, stats in summary.items():
        print(f"  - {domain}: {stats['count']} outcomes, "
              f"{stats['success_rate']:.1%} success, "
              f"{stats['avg_reward']:.3f} avg reward")

    # Example 4: Character aggregation
    print("\n[Example 4] Aggregating by character...")
    char_agg = CharacterAggregator(tracker)
    char_results = char_agg.aggregate_by_character()

    for char_id, result in char_results.items():
        print(f"\n  {char_id}:")
        print(f"    Count: {result.count}")
        print(f"    Success rate: {result.success_rate:.1%}")
        print(f"    Avg reward: {result.avg_reward:.3f}")

    # Example 5: Character ranking
    print("\n[Example 5] Ranking characters...")
    ranking = char_agg.get_character_ranking()
    print("  Characters by average reward:")
    for i, (char_id, reward) in enumerate(ranking, 1):
        print(f"    {i}. {char_id}: {reward:.3f}")

    # Example 6: Time-based aggregation
    print("\n[Example 6] Aggregating recent outcomes...")
    time_agg = TimeWindowAggregator(tracker)
    recent = time_agg.aggregate_last_n_minutes(60)
    print(f"  - Last 60 minutes: {recent.count} outcomes, "
          f"{recent.success_rate:.1%} success rate")

    # Example 7: Custom aggregation by outcome type
    print("\n[Example 7] Custom aggregation by outcome type...")
    custom_agg = CustomAggregator(tracker)
    by_type = custom_agg.aggregate(
        key_fn=lambda o: o.outcome_type.value,
    )
    for outcome_type, result in by_type.items():
        print(f"  - {outcome_type}: {result.count} outcomes")

    # Example 8: Custom aggregation with filtering
    print("\n[Example 8] Custom aggregation of successful outcomes only...")
    success_only = custom_agg.aggregate(
        key_fn=lambda o: o.metadata.get("context", {}).get("character_id", "unknown"),
        filter_fn=lambda o: o.success,
    )
    for char_id, result in success_only.items():
        print(f"  - {char_id}: {result.count} successful outcomes")

    print("\n" + "=" * 60)
    print("Aggregation example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
