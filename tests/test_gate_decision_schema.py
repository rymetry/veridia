"""GateDecision契約テスト(North Star §6.24 / ADR-0007のveridia固有4契約の4本目)。

GateDecisionは **ArtifactBase(§6.1)を継承しない**。producerが決定的評価器であり、
ArtifactBase必須の `confidence` / `created_by.skill` / `created_by.model` に対応する
真実を供給できないため(learning-log「契約の必須度は最初のproducerのDoDと突き合わせる」)。
本ファイルはその設計判断も含めて固定する。
"""

from __future__ import annotations

import copy
import json
from functools import cache
from pathlib import Path
from typing import Any

import pytest
from artifact_validator import ArtifactValidationError, validate_artifact
from jsonschema import Draft202012Validator

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
SCHEMA_FILENAME = "gate-decision.schema.json"
ARTIFACT_TYPE = "gate_decision"
DOMAIN_REQUIRED = {
    "artifact_type",
    "version",
    "gate_id",
    "created_at",
    "policy_version",
    "subject_declared_status",
    "decision",
    "gate_results",
    "blocking_reasons",
    "warning_reasons",
    "evidence_refs",
}


@cache
def load_schema() -> dict[str, Any]:
    return json.loads((SCHEMAS_DIR / SCHEMA_FILENAME).read_text(encoding="utf-8"))


def make_valid_decision() -> dict[str, Any]:
    """schema埋め込みexampleの複製(共有状態を持たない)。"""
    return copy.deepcopy(load_schema()["examples"][0])


class TestSchemaItself:
    def test_schema_is_valid_against_draft_2020_12_metaschema(self) -> None:
        Draft202012Validator.check_schema(load_schema())

    def test_artifact_type_is_fixed_by_const(self) -> None:
        assert load_schema()["properties"]["artifact_type"]["const"] == ARTIFACT_TYPE

    def test_required_matches_expected(self) -> None:
        assert set(load_schema()["required"]) == DOMAIN_REQUIRED

    def test_does_not_inherit_artifact_base(self) -> None:
        # 意図的な非継承。決定的評価器はconfidence / created_by.skill / modelを供給できない
        assert "allOf" not in load_schema()

    def test_does_not_require_confidence(self) -> None:
        assert "confidence" not in load_schema()["properties"]

    def test_is_closed_to_additional_properties(self) -> None:
        assert load_schema()["additionalProperties"] is False

    def test_gate_result_reason_is_required_for_every_outcome(self) -> None:
        # inconclusiveを「黙ってpass扱いにしない」ための最低条件は、理由が必ず残ること
        gate_result = load_schema()["$defs"]["gateResult"]

        assert "reason" in gate_result["required"]
        assert gate_result["properties"]["reason"]["minLength"] == 1

    def test_subject_declared_status_allows_null(self) -> None:
        # 「宣言が無かった」と「見ていない」を区別する。malformed subjectでもnullで記録する
        enum = load_schema()["properties"]["subject_declared_status"]["enum"]

        assert None in enum
        assert {"passed", "passed-with-risks", "blocked"} <= set(enum) - {None}


class TestValidPayload:
    def test_embedded_example_passes(self) -> None:
        validate_artifact(make_valid_decision())

    def test_router_resolves_gate_decision_artifact_type(self) -> None:
        from artifact_validator.schema_store import artifact_type_to_schema

        assert artifact_type_to_schema()[ARTIFACT_TYPE] == SCHEMA_FILENAME

    @pytest.mark.parametrize("decision", ["pass", "warn", "block"])
    def test_every_decision_value_is_accepted(self, decision: str) -> None:
        payload = make_valid_decision()
        payload["decision"] = decision

        validate_artifact(payload)

    def test_release_candidate_may_be_null(self) -> None:
        # Phase 1はrelease candidateではなくrunを評価する(§6.24からの意図的な緩和)
        payload = make_valid_decision()
        payload["release_candidate"] = None

        validate_artifact(payload)

    def test_reason_lists_may_be_empty_on_pass(self) -> None:
        payload = make_valid_decision()
        payload["decision"] = "pass"
        payload["blocking_reasons"] = []
        payload["warning_reasons"] = []

        validate_artifact(payload)


class TestInvalidPayload:
    @pytest.mark.parametrize("field", sorted(DOMAIN_REQUIRED))
    def test_missing_required_field_fails(self, field: str) -> None:
        payload = make_valid_decision()
        del payload[field]

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    def test_unknown_top_level_field_fails(self) -> None:
        payload = make_valid_decision()
        payload["overall_confidence"] = 0.9

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    def test_empty_evidence_refs_fails(self) -> None:
        # 何を評価した決定なのか言えないrecordは監査に使えない
        payload = make_valid_decision()
        payload["evidence_refs"] = []

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    def test_empty_gate_results_fails(self) -> None:
        payload = make_valid_decision()
        payload["gate_results"] = []

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            ("decision", "inconclusive"),
            ("subject_declared_status", "unknown"),
            ("created_at", "2026-08-02T09:00:00"),
            ("policy_version", "0.1"),
            ("version", "v0.1.0"),
            ("gate_id", ""),
        ],
    )
    def test_invalid_field_value_fails(self, field: str, invalid_value: Any) -> None:
        payload = make_valid_decision()
        payload[field] = invalid_value

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            ("gate", ""),
            ("stage", "enforce"),
            ("outcome", "blocked"),
            ("reason", ""),
        ],
    )
    def test_invalid_gate_result_value_fails(self, field: str, invalid_value: Any) -> None:
        payload = make_valid_decision()
        payload["gate_results"][0][field] = invalid_value

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    def test_unknown_gate_result_field_fails(self) -> None:
        payload = make_valid_decision()
        payload["gate_results"][0]["evidence_refs"] = ["run-1"]

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)
