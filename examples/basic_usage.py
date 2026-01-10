"""
Basic Usage Example for Outcome Tracker

This example demonstrates the core functionality of the Outcome Tracker:
- Tracking immediate and delayed outcomes
- Calculating rewards across multiple domains
- Analyzing decision quality
"""

from outcome_tracker import (
    OutcomeTracker,
    RewardDomain,
    OutcomeType,
)


def main():
    """Run the basic usage example."""
    print("=" * 60)
    print("Outcome Tracker - Basic Usage Example")
    print("=" * 60)

    # Initialize the tracker
    tracker = OutcomeTracker()

    # Example 1: Track a combat outcome
    print("\n[Example 1] Tracking a combat outcome...")
    combat_outcome = tracker.track_immediate_outcome(
        decision_id="combat_001",
        description="Hit goblin for 15 damage, goblin defeated",
        success=True,
        context={
            "decision_type": "combat_action",
            "character_id": "thorin",
            "weapon": "sword",
        },
    )
    print(f"  - Tracked {len(combat_outcome.rewards)} reward signals")
    for reward in combat_outcome.rewards:
        print(f"    * {reward.domain.value}: {reward.value:.3f}")

    # Example 2: Track a social interaction
    print("\n[Example 2] Tracking a social interaction...")
    social_outcome = tracker.track_immediate_outcome(
        decision_id="social_001",
        description="Convinced merchant to lower prices, relationship improved +5",
        success=True,
        context={
            "decision_type": "social",
            "character_id": "elara",
            "npc": "merchant",
        },
    )
    print(f"  - Tracked {len(social_outcome.rewards)} reward signals")
    for reward in social_outcome.rewards:
        print(f"    * {reward.domain.value}: {reward.value:.3f}")

    # Example 3: Track an exploration outcome
    print("\n[Example 3] Tracking an exploration outcome...")
    explore_outcome = tracker.track_immediate_outcome(
        decision_id="explore_001",
        description="Discovered hidden treasure chest behind secret door",
        success=True,
        context={
            "decision_type": "exploration",
            "character_id": "thorin",
        },
    )
    print(f"  - Tracked {len(explore_outcome.rewards)} reward signals")

    # Example 4: Track a delayed outcome (after combat)
    print("\n[Example 4] Tracking a delayed outcome...")
    delayed_outcome = tracker.track_delayed_outcome(
        decision_id="combat_001",
        description="Party safe from remaining enemies, gained 50 XP",
        success=True,
        context={"decision_type": "combat_action"},
        outcome_type=OutcomeType.SHORT_TERM,
        related_decisions=["combat_001"],
    )
    print(f"  - Tracked delayed outcome for combat_001")

    # Example 5: Get aggregate reward for a decision
    print("\n[Example 5] Getting aggregate rewards...")
    total_reward = tracker.get_aggregate_reward("combat_001")
    combat_reward = tracker.get_aggregate_reward("combat_001", RewardDomain.COMBAT)
    print(f"  - Total reward for combat_001: {total_reward:.3f}")
    print(f"  - Combat domain reward: {combat_reward:.3f}")

    # Example 6: Analyze decision quality
    print("\n[Example 6] Analyzing decision quality...")
    quality = tracker.analyze_decision_quality("combat_001")
    print(f"  - Quality score: {quality['quality_score']:.3f}")
    print(f"  - Confidence: {quality['confidence']:.2f}")
    print(f"  - Success rate: {quality['success_rate']:.1%}")
    print(f"  - Domain scores:")
    for domain, score in quality.get("domain_scores", {}).items():
        print(f"    * {domain}: {score:.3f}")

    # Example 7: Get overall statistics
    print("\n[Example 7] Getting overall statistics...")
    stats = tracker.get_statistics()
    print(f"  - Total outcomes: {stats['total_outcomes']}")
    print(f"  - Success rate: {stats['success_rate_overall']:.1%}")
    print(f"  - Average reward: {stats['avg_reward_signal']:.3f}")
    print(f"  - Immediate: {stats['immediate_outcomes']}")
    print(f"  - Short-term: {stats['short_term_outcomes']}")
    print(f"  - Long-term: {stats['long_term_outcomes']}")

    # Example 8: Get outcomes for a decision
    print("\n[Example 8] Getting outcomes for a decision...")
    outcomes = tracker.get_outcomes_for_decision("combat_001")
    print(f"  - Found {len(outcomes)} outcomes for combat_001")
    for outcome in outcomes:
        print(f"    * [{outcome.outcome_type.value}] {outcome.description}")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
