"""sqk-core skill I/O contract validation at the veridia boundary.

sqk-core ships valid / invalid fixtures for every schema it owns. Those fixtures are
the regression guard here: veridia must accept exactly what sqk-core accepts, without
copying or rewriting the contracts (`docs/plan/sqk-core-integration.md`).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from artifact_validator import (
    ArtifactValidationError,
    SqkSchemaError,
    sqk_schema_store,
    validate_handoff_envelope,
    validate_sqk_artifact,
)
from artifact_validator.sqk_schema_store import (
    SQK_SCHEMAS_DIR,
    available_schema_refs,
    resolve_schema_path,
)

FIXTURES_DIR = SQK_SCHEMAS_DIR / "tests" / "fixtures"
SCHEMA_SUFFIX = ".schema.json"
REQUIRE_SQK_ENV = "VERIDIA_REQUIRE_SQK"

_SQK_AVAILABLE = bool(available_schema_refs())

# Locally the submodule may be absent and skipping is the right behaviour. In CI it is not:
# a silently skipped module means the sqk-core contract boundary went unverified while the
# run stayed green. CI sets VERIDIA_REQUIRE_SQK=1 to turn that skip into a collection error.
if not _SQK_AVAILABLE and os.environ.get(REQUIRE_SQK_ENV):
    raise RuntimeError(
        f"{REQUIRE_SQK_ENV} is set but no sqk-core schema was found under {SQK_SCHEMAS_DIR}. "
        "the submodule was not checked out: run `git submodule update --init --recursive` "
        "(in CI, set `submodules: true` on actions/checkout)"
    )

pytestmark = pytest.mark.skipif(
    not _SQK_AVAILABLE,
    reason="vendor/sqk-core submodule not checked out",
)


def _fixture_cases(kind: str) -> list[tuple[str, Path]]:
    """Collect (schema_ref, fixture path) for every sqk-core fixture of one kind."""
    cases = []
    for schema_dir in sorted(FIXTURES_DIR.iterdir()):
        if not (schema_dir / kind).is_dir():
            continue
        schema_ref = f"schemas/{schema_dir.name}{SCHEMA_SUFFIX}"
        for fixture in sorted((schema_dir / kind).glob("*.json")):
            cases.append((schema_ref, fixture))
    return cases


def _case_id(case: tuple[str, Path]) -> str:
    schema_ref, fixture = case
    return f"{Path(schema_ref).name.removesuffix(SCHEMA_SUFFIX)}/{fixture.stem}"


def _load(fixture: Path) -> dict:
    return json.loads(fixture.read_text(encoding="utf-8"))


class TestSqkFixtureContract:
    """Every sqk-core fixture must round-trip through the veridia validator."""

    def test_fixture_corpus_is_not_empty(self) -> None:
        assert _fixture_cases("valid"), "sqk-core valid fixtures were not discovered"
        assert _fixture_cases("invalid"), "sqk-core invalid fixtures were not discovered"

    @pytest.mark.parametrize("case", _fixture_cases("valid"), ids=_case_id)
    def test_valid_fixture_passes(self, case: tuple[str, Path]) -> None:
        schema_ref, fixture = case
        validate_sqk_artifact(_load(fixture), schema_ref=schema_ref)

    @pytest.mark.parametrize("case", _fixture_cases("invalid"), ids=_case_id)
    def test_invalid_fixture_is_rejected(self, case: tuple[str, Path]) -> None:
        schema_ref, fixture = case
        with pytest.raises(ArtifactValidationError):
            validate_sqk_artifact(_load(fixture), schema_ref=schema_ref)


class TestHandoffEnvelope:
    """The envelope is the transport; carried artifacts are validated per schema_ref."""

    def test_envelope_and_payloads_pass(self) -> None:
        """Happy path composed from sqk-core's own per-item fixture.

        Composed rather than read from `handoff-envelope/valid/`: that fixture carries an
        under-populated payload (see `test_envelope_payload_gap_in_sqk_core_fixture`).
        """
        risk_item = _load(next((FIXTURES_DIR / "risk-item" / "valid").glob("*.json")))
        envelope = {
            "source_skill": "risk-analysis",
            "phase": "risk-analysis",
            "artifacts": [
                {
                    "type": "RiskItemList",
                    "schema_ref": "schemas/risk-item.schema.json",
                    "items": [risk_item],
                }
            ],
            "trace_ids": ["REQ-012", "RISK-007"],
            "assumptions": [],
            "open_questions": [],
            "gate_status": "passed-with-risks",
        }
        validate_handoff_envelope(envelope)

    def test_envelope_payload_gap_in_sqk_core_fixture(self) -> None:
        """sqk-core's `handoff-envelope` valid fixture carries an invalid RiskItem payload.

        sqk-core's own harness (`scripts/validate-schemas.sh`) checks each fixture against
        its own schema only, and `handoff-envelope.artifacts[].items` is an unconstrained
        array, so the embedded payload is never checked against the `schema_ref` it declares.
        The embedded item has `id` + `statement` but `risk-item.schema.json` also requires
        `category` / `likelihood` / `impact` / `treatment`.

        Reported upstream per `docs/plan/sqk-core-integration.md` §5. This test pins the
        current behaviour; remove it once the sqk-core fixture is corrected and the SHA
        is bumped.
        """
        envelope = _load(FIXTURES_DIR / "handoff-envelope" / "valid" / "risk-analysis-handoff.json")
        with pytest.raises(ArtifactValidationError) as excinfo:
            validate_handoff_envelope(envelope)
        missing = {issue.field_path for issue in excinfo.value.errors}
        assert missing == {
            "$.artifacts[0].items[0].category",
            "$.artifacts[0].items[0].likelihood",
            "$.artifacts[0].items[0].impact",
            "$.artifacts[0].items[0].treatment",
        }

    def test_envelope_shape_alone_accepts_that_fixture(self) -> None:
        """The same fixture is valid as an envelope: the gap is only visible at payload level."""
        envelope = _load(FIXTURES_DIR / "handoff-envelope" / "valid" / "risk-analysis-handoff.json")
        validate_sqk_artifact(envelope, schema_ref="schemas/handoff-envelope.schema.json")

    def test_broken_envelope_shape_is_reported(self) -> None:
        envelope = _load(
            FIXTURES_DIR / "handoff-envelope" / "invalid" / "gate-status-enum-violation.json"
        )
        with pytest.raises(ArtifactValidationError) as excinfo:
            validate_handoff_envelope(envelope)
        assert any(issue.field_path == "$.gate_status" for issue in excinfo.value.errors)

    def test_carried_item_failure_reports_nested_path(self) -> None:
        envelope = _load(FIXTURES_DIR / "handoff-envelope" / "valid" / "risk-analysis-handoff.json")
        broken = {
            **envelope,
            "artifacts": [
                {
                    **envelope["artifacts"][0],
                    "items": [{"id": "NOT-A-RISK-ID", "statement": "壊れたID"}],
                }
            ],
        }
        with pytest.raises(ArtifactValidationError) as excinfo:
            validate_handoff_envelope(broken)
        assert any(
            issue.field_path == "$.artifacts[0].items[0].id" for issue in excinfo.value.errors
        )

    def test_content_shaped_artifact_is_validated(self) -> None:
        matrix = _load(
            next((FIXTURES_DIR / "condition-assignment-matrix" / "valid").glob("*.json"))
        )
        envelope = {
            "source_skill": "test-architecture-design",
            "phase": "TAD",
            "artifacts": [
                {
                    "type": "ConditionAssignmentMatrix",
                    "schema_ref": "schemas/condition-assignment-matrix.schema.json",
                    "content": matrix,
                }
            ],
            "trace_ids": ["DTC-001"],
            "assumptions": [],
            "open_questions": [],
            "gate_status": "passed",
        }
        validate_handoff_envelope(envelope)

    def test_paths_stay_precise_across_multiple_artifacts_and_items(self) -> None:
        """Both the artifact index and the item index must survive into the reported path.

        Gap found by running `test-architecture-design` on this feature (DTC-008): the
        prior nested-path test only covered `artifacts[0].items[0]`, so an index bug on
        either axis would not have been observable.
        """
        valid_item = _load(next((FIXTURES_DIR / "risk-item" / "valid").glob("*.json")))
        bad_id_item = {**valid_item, "id": "NOT-A-RISK-ID"}
        missing_fields_item = {"id": "RISK-042", "statement": "必須欄が欠けたリスク"}
        envelope = {
            "source_skill": "risk-analysis",
            "phase": "risk-analysis",
            "artifacts": [
                {
                    "type": "RiskItemList",
                    "schema_ref": "schemas/risk-item.schema.json",
                    "items": [valid_item, bad_id_item],
                },
                {
                    "type": "RiskItemList",
                    "schema_ref": "schemas/risk-item.schema.json",
                    "items": [missing_fields_item, valid_item],
                },
            ],
            "trace_ids": ["RISK-007"],
            "assumptions": [],
            "open_questions": [],
            "gate_status": "blocked",
        }

        with pytest.raises(ArtifactValidationError) as excinfo:
            validate_handoff_envelope(envelope)

        reported = {issue.field_path for issue in excinfo.value.errors}
        assert "$.artifacts[0].items[1].id" in reported
        assert "$.artifacts[1].items[0].category" in reported
        # the valid items must contribute nothing
        assert not {path for path in reported if path.startswith("$.artifacts[0].items[0]")}
        assert not {path for path in reported if path.startswith("$.artifacts[1].items[1]")}

    def test_broken_envelope_skips_payload_validation(self) -> None:
        """A broken envelope must not produce payload paths into a structure that does not hold.

        Gap found by running `test-architecture-design` on this feature (DTC-010): the
        early return was implemented but never exercised.
        """
        envelope = {
            "source_skill": "risk-analysis",
            "phase": "risk-analysis",
            "artifacts": [
                {
                    "type": "RiskItemList",
                    "schema_ref": "schemas/risk-item.schema.json",
                    "items": [{"id": "RISK-042", "statement": "必須欄が欠けたリスク"}],
                }
            ],
            "trace_ids": ["RISK-042"],
            "assumptions": [],
            "open_questions": [],
            "gate_status": "not-a-gate-status",
        }

        with pytest.raises(ArtifactValidationError) as excinfo:
            validate_handoff_envelope(envelope)

        reported = {issue.field_path for issue in excinfo.value.errors}
        assert reported == {"$.gate_status"}


class TestSchemaResolution:
    """Contract-unavailable failures are distinct from validation failures, and loud."""

    def test_unknown_schema_ref_lists_supported_refs(self) -> None:
        with pytest.raises(SqkSchemaError) as excinfo:
            resolve_schema_path("schemas/does-not-exist.schema.json")
        message = str(excinfo.value)
        assert "unknown schema_ref" in message
        assert "schemas/test-case.schema.json" in message

    def test_traversal_outside_schema_dir_is_rejected(self) -> None:
        with pytest.raises(SqkSchemaError, match="escapes the sqk-core schema directory"):
            resolve_schema_path("schemas/../../../etc/passwd")

    def test_ref_outside_schemas_prefix_is_rejected(self) -> None:
        with pytest.raises(SqkSchemaError, match="must start with"):
            resolve_schema_path("docs/README.md")

    def test_missing_submodule_names_the_fix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sqk_schema_store, "SQK_SCHEMAS_DIR", Path("/nonexistent/sqk-core"))
        with pytest.raises(SqkSchemaError) as excinfo:
            resolve_schema_path("schemas/test-case.schema.json")
        assert "git submodule update --init --recursive" in str(excinfo.value)
