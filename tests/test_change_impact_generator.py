"""T-010 ChangeImpactSpec generatorの契約テスト。"""

from __future__ import annotations

import json
from pathlib import Path

from artifact_validator import validate_artifact

FIXTURE_DIFF = Path(__file__).parent / "fixtures" / "change_impact" / "sample.diff"


def test_cli_generates_valid_change_impact_spec_from_sample_diff(tmp_path: Path) -> None:
    from change_impact_generator.cli import main

    output_path = tmp_path / "change-impact-spec.json"

    assert main([str(FIXTURE_DIFF), str(output_path), "--source-ref", "fixture://sample-pr"]) == 0

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    validate_artifact(artifact)
    assert artifact["artifact_type"] == "change_impact_spec"
    assert artifact["source_refs"] == ["fixture://sample-pr"]


def test_generator_includes_file_and_component_candidates() -> None:
    from change_impact_generator import generate_change_impact_spec

    diff_text = FIXTURE_DIFF.read_text(encoding="utf-8")

    artifact = generate_change_impact_spec(diff_text, source_ref="fixture://sample-pr")

    assert {
        "path": "src/order/cancel_order.py",
        "change_type": "modified",
        "risk_level": "medium",
        "component": "order",
        "lines_added": 2,
        "lines_deleted": 0,
    }.items() <= artifact["changed_files"][0].items()
    assert {
        "path": "qa-skills/payments/README.md",
        "change_type": "added",
        "risk_level": "medium",
        "component": "qa-skills/payments",
        "lines_added": 3,
        "lines_deleted": 0,
    }.items() <= artifact["changed_files"][1].items()
    assert artifact["changed_components"] == ["order", "qa-skills/payments"]
    assert artifact["impacted_requirements"] == []
    assert artifact["impacted_risks"] == []
    assert artifact["impacted_apis"] == []
    assert artifact["confidence"] == 0.4
    assert artifact["requires_human_review"] is True


def test_generator_is_deterministic_for_same_input() -> None:
    from change_impact_generator import generate_change_impact_spec

    diff_text = FIXTURE_DIFF.read_text(encoding="utf-8")

    first = generate_change_impact_spec(diff_text, source_ref="fixture://sample-pr")
    second = generate_change_impact_spec(diff_text, source_ref="fixture://sample-pr")

    assert first == second
    assert first["created_at"] == "1970-01-01T00:00:00Z"
    assert first["change_impact_id"].startswith("CIS-")
