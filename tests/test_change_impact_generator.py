"""T-010 ChangeImpactSpec generatorの契約テスト。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from artifact_validator import ArtifactValidationError, validate_artifact
from trace_ids import TRACE_ID_RE

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
    assert TRACE_ID_RE.fullmatch(first["trace_id"])


def test_diff_parser_counts_hunk_content_lines_that_look_like_file_headers() -> None:
    from change_impact_generator.diff_parser import parse_unified_diff

    diff_text = """\
diff --git a/db/query.sql b/db/query.sql
index 1111111..2222222 100644
--- a/db/query.sql
+++ b/db/query.sql
@@ -1,3 +1,3 @@
 SELECT 1;
--- old comment
+++ i;
"""

    (changed,) = parse_unified_diff(diff_text)

    assert changed.path == "db/query.sql"
    assert changed.lines_deleted == 1
    assert changed.lines_added == 1


def test_diff_parser_decodes_quoted_non_ascii_paths() -> None:
    from change_impact_generator.diff_parser import parse_unified_diff

    diff_text = """\
diff --git "a/docs/\\346\\227\\245\\346\\234\\254.md" "b/docs/\\346\\227\\245\\346\\234\\254.md"
index 1111111..2222222 100644
--- "a/docs/\\346\\227\\245\\346\\234\\254.md"
+++ "b/docs/\\346\\227\\245\\346\\234\\254.md"
@@ -1 +1 @@
-old
+new
"""

    (changed,) = parse_unified_diff(diff_text)

    assert changed.path == "docs/日本.md"
    assert changed.lines_deleted == 1
    assert changed.lines_added == 1


def test_diff_parser_preserves_unquoted_paths_with_spaces_without_file_headers() -> None:
    from change_impact_generator.diff_parser import parse_unified_diff

    diff_text = """\
diff --git a/docs/my note.md b/docs/my note.md
similarity index 100%
rename from docs/my note.md
rename to docs/my renamed note.md
"""

    (changed,) = parse_unified_diff(diff_text)

    assert changed.path == "docs/my renamed note.md"
    assert changed.old_path == "docs/my note.md"
    assert changed.change_type == "renamed"


def test_diff_parser_handles_delete_diff() -> None:
    from change_impact_generator.diff_parser import parse_unified_diff

    diff_text = """\
diff --git a/src/obsolete.py b/src/obsolete.py
deleted file mode 100644
index 1111111..0000000
--- a/src/obsolete.py
+++ /dev/null
@@ -1,2 +0,0 @@
-print("old")
-print("gone")
"""

    (changed,) = parse_unified_diff(diff_text)

    assert changed.path == "src/obsolete.py"
    assert changed.old_path is None
    assert changed.change_type == "deleted"
    assert changed.lines_deleted == 2
    assert changed.lines_added == 0


def test_diff_parser_rejects_invalid_quoted_path_escape() -> None:
    from change_impact_generator.diff_parser import parse_unified_diff

    diff_text = 'diff --git "a/docs/\\q.md" "b/docs/\\q.md"\n'

    with pytest.raises(ValueError, match="escape"):
        parse_unified_diff(diff_text)


def test_diff_header_path_splitter_rejects_empty_header_payload() -> None:
    from change_impact_generator.diff_parser import _split_diff_header_paths

    with pytest.raises(ValueError, match="malformed diff header"):
        _split_diff_header_paths("")


def test_cli_returns_validation_error_when_generated_artifact_is_invalid(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import change_impact_generator.cli as cli

    diff_path = tmp_path / "input.diff"
    output_path = tmp_path / "out.json"
    diff_path.write_text(FIXTURE_DIFF.read_text(encoding="utf-8"), encoding="utf-8")

    def reject(_artifact: object) -> None:
        raise ArtifactValidationError(())

    monkeypatch.setattr(cli, "validate_artifact", reject)

    assert cli.main([str(diff_path), str(output_path)]) == 1
    assert "invalid generated artifact" in capsys.readouterr().err


def test_cli_still_returns_input_error_for_missing_diff_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from change_impact_generator.cli import main

    assert main([str(tmp_path / "missing.diff"), str(tmp_path / "out.json")]) == 2
    assert "error:" in capsys.readouterr().err
