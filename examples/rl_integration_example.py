"""
Reinforcement Learning Integration Example

This example demonstrates how to use the Outcome Tracker in a reinforcement
learning context, where agents make decisions and receive rewards based on
their outcomes.
"""

import random
from outcome_tracker import (
    OutcomeTracker,
    RewardDomain,
    OutcomeType,
)


class SimpleAgent:
    """A simple agent that makes decisions."""

    def __init__(self, name: str):
        self.name = name

    def decide_action(self, context: dict) -> str:
        """Choose an action based on context."""
        actions = ["attack", "negotiate", "explore", "retreat"]
        # Simple random policy
        return random.choice(actions)

    def execute_action(self, action: str, context: dict) -> tuple[bool, str]:
        """Execute an action and return (success, description)."""
        # Simulate action outcomes
        if action == "attack":
            success = random.random() > 0.3  # 70% success rate
            if success:
                damage = random.randint(10, 25)
                return True, f"Hit enemy for {damage} damage, enemy defeated"
            else:
                return False, "Attack missed"

        elif action == "negotiate":
            success = random.random() > 0.4  # 60% success rate
            if success:
                return True, "Convinced opponent to back down peacefully"
            else:
                return False, "Negotiation failed, opponent hostile"

        elif action == "explore":
            success = random.random() > 0.2  # 80% success rate
            if success:
                discoveries = ["secret door", "hidden treasure", "ancient artifact"]
                found = random.choice(discoveries)
                return True, f"Discovered {found}"
            else:
                return False, "Found nothing of interest"

        elif action == "retreat":
            return True, "Safely retreated from danger"

        return False, "Unknown action"


def simulate_episode(tracker: OutcomeTracker, agent: SimpleAgent, episode_id: str):
    """Simulate one episode of agent behavior."""
    print(f"\n--- Episode {episode_id} ---")

    # Multiple decisions per episode
    for step in range(1, 4):
        decision_id = f"{episode_id}_step{step}"

        # Agent makes a decision
        context = {
            "decision_type": random.choice(["combat_action", "social", "exploration"]),
            "character_id": agent.name,
            "episode": episode_id,
            "step": step,
        }

        action = agent.decide_action(context)
        print(f"  Step {step}: {agent.name} chooses to {action}")

        # Execute and track immediate outcome
        success, description = agent.execute_action(action, context)

        outcome = tracker.track_immediate_outcome(
            decision_id=decision_id,
            description=description,
            success=success,
            context=context,
        )

        # Show reward
        if outcome.rewards:
            avg_reward = sum(r.value for r in outcome.rewards) / len(outcome.rewards)
            print(f"    Outcome: {description}")
            print(f"    Reward: {avg_reward:.3f}")

        # Track delayed outcome for some decisions
        if success and random.random() > 0.5:
            tracker.track_delayed_outcome(
                decision_id=decision_id,
                description=f"Gained resources and XP from {action}",
                success=True,
                context=context,
                outcome_type=OutcomeType.SHORT_TERM,
            )


def analyze_agent_performance(tracker: OutcomeTracker, agent_name: str):
    """Analyze and display agent performance."""
    print(f"\n=== Performance Analysis for {agent_name} ===")

    # Get overall statistics
    stats = tracker.get_statistics()
    print(f"Total outcomes tracked: {stats['total_outcomes']}")
    print(f"Overall success rate: {stats['success_rate_overall']:.1%}")
    print(f"Average reward: {stats['avg_reward_signal']:.3f}")

    # Get domain breakdown
    from outcome_tracker.aggregators import DomainAggregator
    domain_agg = DomainAggregator(tracker)
    summary = domain_agg.get_domain_summary()

    print("\nPerformance by domain:")
    for domain, domain_stats in summary.items():
        print(f"  {domain}:")
        print(f"    Count: {domain_stats['count']}")
        print(f"    Success rate: {domain_stats['success_rate']:.1%}")
        print(f"    Avg reward: {domain_stats['avg_reward']:.3f}")


def main():
    """Run the RL integration example."""
    print("=" * 60)
    print("Outcome Tracker - RL Integration Example")
    print("=" * 60)

    # Initialize tracker and agents
    tracker = OutcomeTracker()
    agent1 = SimpleAgent("Thorin")
    agent2 = SimpleAgent("Elara")

    # Simulate multiple episodes
    for episode_num in range(1, 6):
        episode_id = f"ep{episode_num:02d}"

        # Alternate between agents
        agent = agent1 if episode_num % 2 == 1 else agent2
        simulate_episode(tracker, agent, episode_id)

    # Analyze overall performance
    print("\n" + "=" * 60)
    print("SESSION SUMMARY")
    print("=" * 60)

    analyze_agent_performance(tracker, "All Agents")

    # Show best/worst performing decisions
    print("\n=== Top 3 Decisions by Quality ===")
    all_decisions = list(tracker.outcomes.keys())
    decision_qualities = [
        (dec_id, tracker.analyze_decision_quality(dec_id))
        for dec_id in all_decisions
    ]
    decision_qualities.sort(key=lambda x: x[1]["quality_score"], reverse=True)

    for i, (dec_id, quality) in enumerate(decision_qualities[:3], 1):
        print(f"{i}. {dec_id}")
        print(f"   Quality: {quality['quality_score']:.3f} "
              f"(confidence: {quality['confidence']:.2f})")

    # Show causal chains if any
    if tracker.causal_chains:
        print("\n=== Causal Chains Detected ===")
        for i, chain in enumerate(tracker.causal_chains[:3], 1):
            print(f"{i}. {' -> '.join(chain)}")

    # Export session data
    print("\n=== Exporting Session Data ===")
    from outcome_tracker.exporters import PrettyPrinter
    printer = PrettyPrinter(tracker)
    printer.print_summary()

    print("\n" + "=" * 60)
    print("RL integration example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
