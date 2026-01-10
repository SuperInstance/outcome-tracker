"""Tests for the exporters module."""

import pytest
import json
import tempfile
import csv
from pathlib import Path
from outcome_tracker import (
    OutcomeTracker,
    RewardDomain,
    OutcomeType,
)
from outcome_tracker.exporters import (
    JSONExporter,
    CSVExporter,
    PrettyPrinter,
    ExportFormat,
    export_outcomes,
)


class TestJSONExporter:
    """Tests for JSONExporter class."""

    @pytest.fixture
    def tracker_with_data(self):
        """Create a tracker with sample data."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="test_001",
            description="Hit for 15 damage",
            success=True,
            context={"decision_type": "combat_action", "character_id": "thorin"},
        )

        tracker.track_delayed_outcome(
            decision_id="test_001",
            description="Gained 50 XP",
            success=True,
            context={"decision_type": "combat_action"},
            outcome_type=OutcomeType.SHORT_TERM,
        )

        return tracker

    def test_export_to_file(self, tracker_with_data):
        """Test exporting to a JSON file."""
        exporter = JSONExporter(tracker_with_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            exporter.export(filepath)
            assert Path(filepath).exists()

            with open(filepath, "r") as f:
                data = json.load(f)

            assert "outcomes" in data
            assert "statistics" in data
            assert len(data["outcomes"]) == 2
        finally:
            Path(filepath).unlink()

    def test_export_with_indent(self, tracker_with_data):
        """Test exporting with indentation."""
        exporter = JSONExporter(tracker_with_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            exporter.export(filepath, indent=2)

            with open(filepath, "r") as f:
                content = f.read()

            # Check that it's formatted with indentation
            assert "\n" in content
            assert "  " in content
        finally:
            Path(filepath).unlink()

    def test_export_by_decision(self, tracker_with_data):
        """Test exporting outcomes for a specific decision."""
        exporter = JSONExporter(tracker_with_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_by_decision(filepath, "test_001")

            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["decision_id"] == "test_001"
            assert len(data["outcomes"]) == 2
            assert "aggregate_reward" in data
            assert "quality_analysis" in data
        finally:
            Path(filepath).unlink()

    def test_export_by_domain(self, tracker_with_data):
        """Test exporting outcomes filtered by domain."""
        exporter = JSONExporter(tracker_with_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_by_domain(filepath, RewardDomain.COMBAT)

            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["domain"] == "combat"
            assert data["count"] > 0
        finally:
            Path(filepath).unlink()

    def test_export_to_string(self, tracker_with_data):
        """Test exporting to a JSON string."""
        exporter = JSONExporter(tracker_with_data)

        json_str = exporter.export_to_string()

        assert isinstance(json_str, str)

        data = json.loads(json_str)
        assert "outcomes" in data


class TestCSVExporter:
    """Tests for CSVExporter class."""

    @pytest.fixture
    def tracker_with_data(self):
        """Create a tracker with sample data."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="csv_001",
            description="Combat success",
            success=True,
            context={"decision_type": "combat_action", "character_id": "thorin"},
        )

        tracker.track_immediate_outcome(
            decision_id="csv_002",
            description="Social failure",
            success=False,
            context={"decision_type": "social", "character_id": "elara"},
        )

        return tracker

    def test_export_to_file(self, tracker_with_data):
        """Test exporting to a CSV file."""
        exporter = CSVExporter(tracker_with_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = f.name

        try:
            exporter.export(filepath)
            assert Path(filepath).exists()

            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
        finally:
            Path(filepath).unlink()

    def test_export_with_custom_columns(self, tracker_with_data):
        """Test exporting with custom columns."""
        exporter = CSVExporter(tracker_with_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = f.name

        try:
            columns = ["decision_id", "success", "timestamp"]
            exporter.export(filepath, columns=columns)

            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert set(rows[0].keys()) <= set(columns)
        finally:
            Path(filepath).unlink()

    def test_export_by_decision(self, tracker_with_data):
        """Test exporting outcomes for a specific decision."""
        exporter = CSVExporter(tracker_with_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_by_decision(filepath, "csv_001")

            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            assert rows[0]["decision_id"] == "csv_001"
        finally:
            Path(filepath).unlink()

    def test_export_summary(self, tracker_with_data):
        """Test exporting a summary CSV."""
        exporter = CSVExporter(tracker_with_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = f.name

        try:
            exporter.export_summary(filepath)

            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2  # Two decisions
            assert "decision_id" in rows[0]
            assert "success_rate" in rows[0]
        finally:
            Path(filepath).unlink()


class TestPrettyPrinter:
    """Tests for PrettyPrinter class."""

    @pytest.fixture
    def tracker_with_data(self):
        """Create a tracker with sample data."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="print_001",
            description="Combat success",
            success=True,
            context={"decision_type": "combat_action", "character_id": "thorin"},
        )

        tracker.track_immediate_outcome(
            decision_id="print_002",
            description="Social failure",
            success=False,
            context={"decision_type": "social", "character_id": "elara"},
        )

        return tracker

    def test_print_summary(self, tracker_with_data, capsys):
        """Test printing summary."""
        printer = PrettyPrinter(tracker_with_data)
        printer.print_summary()

        captured = capsys.readouterr()
        assert "OUTCOME TRACKER SUMMARY" in captured.out
        assert "Total Outcomes:" in captured.out
        assert "Success Rate:" in captured.out

    def test_print_decision_outcomes(self, tracker_with_data, capsys):
        """Test printing decision outcomes."""
        printer = PrettyPrinter(tracker_with_data)
        printer.print_decision_outcomes("print_001")

        captured = capsys.readouterr()
        assert "DECISION: print_001" in captured.out
        assert "Quality Score:" in captured.out

    def test_print_decision_outcomes_not_found(self, tracker_with_data, capsys):
        """Test printing outcomes for non-existent decision."""
        printer = PrettyPrinter(tracker_with_data)
        printer.print_decision_outcomes("nonexistent")

        captured = capsys.readouterr()
        assert "No outcomes found" in captured.out

    def test_print_domain_summary(self, tracker_with_data, capsys):
        """Test printing domain summary."""
        printer = PrettyPrinter(tracker_with_data)
        printer.print_domain_summary()

        captured = capsys.readouterr()
        assert "DOMAIN SUMMARY" in captured.out


class TestExportFunction:
    """Tests for the export_outcomes convenience function."""

    @pytest.fixture
    def tracker_with_data(self):
        """Create a tracker with sample data."""
        tracker = OutcomeTracker()

        tracker.track_immediate_outcome(
            decision_id="func_001",
            description="Test outcome",
            success=True,
            context={"decision_type": "combat_action"},
        )

        return tracker

    def test_export_json(self, tracker_with_data):
        """Test export_outcomes with JSON format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            export_outcomes(tracker_with_data, filepath, format="json")
            assert Path(filepath).exists()

            with open(filepath, "r") as f:
                data = json.load(f)

            assert "outcomes" in data
        finally:
            Path(filepath).unlink()

    def test_export_csv(self, tracker_with_data):
        """Test export_outcomes with CSV format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = f.name

        try:
            export_outcomes(tracker_with_data, filepath, format="csv")
            assert Path(filepath).exists()
        finally:
            Path(filepath).unlink()

    def test_export_with_enum(self, tracker_with_data):
        """Test export_outcomes with ExportFormat enum."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            export_outcomes(tracker_with_data, filepath, format=ExportFormat.JSON)
            assert Path(filepath).exists()
        finally:
            Path(filepath).unlink()

    def test_export_invalid_format(self, tracker_with_data):
        """Test export_outcomes with invalid format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            filepath = f.name

        try:
            with pytest.raises(ValueError):
                export_outcomes(tracker_with_data, filepath, format="invalid")
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()
