"""
Export Example for Outcome Tracker

This example demonstrates how to export outcome data to various formats
including JSON, CSV, and pretty-printed summaries.
"""

import tempfile
from pathlib import Path
from outcome_tracker import OutcomeTracker, RewardDomain
from outcome_tracker.exporters import (
    JSONExporter,
    CSVExporter,
    PrettyPrinter,
    export_outcomes,
)


def setup_tracker():
    """Create a tracker with sample data."""
    tracker = OutcomeTracker()

    # Add various outcomes
    tracker.track_immediate_outcome(
        decision_id="combat_001",
        description="Defeated goblin, gained 15 XP",
        success=True,
        context={"decision_type": "combat_action", "character_id": "thorin"},
    )

    tracker.track_immediate_outcome(
        decision_id="social_001",
        description="Convinced merchant to share information",
        success=True,
        context={"decision_type": "social", "character_id": "elara"},
    )

    tracker.track_immediate_outcome(
        decision_id="explore_001",
        description="Found secret passage",
        success=True,
        context={"decision_type": "exploration", "character_id": "thorin"},
    )

    tracker.track_delayed_outcome(
        decision_id="combat_001",
        description="Looted 50 gold from goblin",
        success=True,
        context={"decision_type": "combat_action"},
        outcome_type=OutcomeType.SHORT_TERM,
    )

    return tracker


def main():
    """Run the export example."""
    print("=" * 60)
    print("Outcome Tracker - Export Example")
    print("=" * 60)

    tracker = setup_tracker()

    # Example 1: Pretty print summary
    print("\n[Example 1] Pretty printing summary...")
    printer = PrettyPrinter(tracker)
    printer.print_summary()

    # Example 2: Pretty print decision outcomes
    print("\n[Example 2] Pretty printing decision outcomes...")
    printer.print_decision_outcomes("combat_001")

    # Example 3: Pretty print domain summary
    print("\n[Example 3] Pretty printing domain summary...")
    printer.print_domain_summary()

    # Example 4: Export to JSON (using temporary file)
    print("\n[Example 4] Exporting to JSON...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json_path = f.name

    try:
        json_exporter = JSONExporter(tracker)
        json_exporter.export(json_path, indent=2)
        print(f"  - Exported to: {json_path}")
        print(f"  - File size: {Path(json_path).stat().st_size} bytes")

        # Show first few lines
        with open(json_path, "r") as f:
            lines = f.readlines()
            print(f"  - Preview (first 5 lines):")
            for line in lines[:5]:
                print(f"    {line.rstrip()}")
    finally:
        Path(json_path).unlink(missing_ok=True)

    # Example 5: Export specific decision to JSON
    print("\n[Example 5] Exporting specific decision to JSON...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        decision_json_path = f.name

    try:
        json_exporter.export_by_decision(decision_json_path, "combat_001")
        print(f"  - Exported combat_001 to: {decision_json_path}")
    finally:
        Path(decision_json_path).unlink(missing_ok=True)

    # Example 6: Export domain-filtered to JSON
    print("\n[Example 6] Exporting combat domain to JSON...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        domain_json_path = f.name

    try:
        json_exporter.export_by_domain(domain_json_path, RewardDomain.COMBAT)
        print(f"  - Exported combat outcomes to: {domain_json_path}")
    finally:
        Path(domain_json_path).unlink(missing_ok=True)

    # Example 7: Export to CSV
    print("\n[Example 7] Exporting to CSV...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        csv_path = f.name

    try:
        csv_exporter = CSVExporter(tracker)
        csv_exporter.export(csv_path)
        print(f"  - Exported to: {csv_path}")
        print(f"  - File size: {Path(csv_path).stat().st_size} bytes")

        # Show first few lines
        with open(csv_path, "r") as f:
            lines = f.readlines()
            print(f"  - Preview (first 5 lines):")
            for line in lines[:5]:
                print(f"    {line.rstrip()}")
    finally:
        Path(csv_path).unlink(missing_ok=True)

    # Example 8: Export summary to CSV
    print("\n[Example 8] Exporting summary to CSV...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        summary_csv_path = f.name

    try:
        csv_exporter.export_summary(summary_csv_path)
        print(f"  - Exported summary to: {summary_csv_path}")

        with open(summary_csv_path, "r") as f:
            print(f"  - Contents:")
            for line in f:
                print(f"    {line.rstrip()}")
    finally:
        Path(summary_csv_path).unlink(missing_ok=True)

    # Example 9: Export with flattened reward columns
    print("\n[Example 9] Exporting to CSV with flattened rewards...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        flat_csv_path = f.name

    try:
        csv_exporter.export(flat_csv_path, flatten_rewards=True)
        print(f"  - Exported with flattened rewards to: {flat_csv_path}")
    finally:
        Path(flat_csv_path).unlink(missing_ok=True)

    # Example 10: Using the convenience function
    print("\n[Example 10] Using export_outcomes convenience function...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        conv_path = f.name

    try:
        export_outcomes(tracker, conv_path, format="json", indent=2)
        print(f"  - Exported using convenience function to: {conv_path}")
    finally:
        Path(conv_path).unlink(missing_ok=True)

    print("\n" + "=" * 60)
    print("Export example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
