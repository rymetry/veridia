"""ExecutionEvidence schemaの契約テスト。

T-005 DoD:
- schemaが存在し、`allOf` で artifact-base を継承している
- §6.23のfield構成に準拠し、test実行結果・state diff・logsへの参照を表現できる
- 有効サンプルがpassし、不正サンプルがfailする

North Star参照: §6.23(ExecutionEvidence)、§15.3(Evidence Storeの保存対象)。
"""

from __future__ import annotations

from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from tests.test_artifact_base_schema import SECTION_6_1_REQUIRED_FIELDS
from tests.test_core_spec_schemas import (
    SCHEMAS_DIR,
    load_schema,
    make_base_fields,
    validator_for,
)

SCHEMA_FILENAME = "execution-evidence.schema.json"
TITLE = "ExecutionEvidence"
ARTIFACT_TYPE = "execution_evidence"
DOMAIN_REQUIRED_FIELDS = frozenset(
    {
        "run_id",
        "test_asset_id",
        "environment",
        "inputs",
        "outputs",
        "state_before",
        "state_after",
        "state_diff",
        "tool_calls",
        "logs",
        "screenshots",
        "grader_results",
        "verdict",
        "reproduction_bundle",
    }
)


def make_valid_instance() -> dict[str, Any]:
    """§6.23のfield構成を満たす有効なExecutionEvidence instance。"""
    return {
        **make_base_fields(ARTIFACT_TYPE),
        "artifact_id": "ART-EVIDENCE-001",
        "source_refs": ["internal://test-assets/TEST-ORDER-CANCEL-001"],
        "created_by": {
            "agent": "execution-agent",
            "skill": "execution-evidence-capture",
            "model": "claude-fable-5",
        },
        "confidence": 0.9,
        "run_id": "RUN-20260702-001",
        "test_asset_id": "TEST-ORDER-CANCEL-001",
        "environment": {
            "env_id": "sandbox-789",
            "seed": "fixture-order-paid-v3",
            "clock": "2026-07-02T10:00:00+09:00",
        },
        "inputs": {"fixture_ref": "object-storage://evidence/RUN-20260702-001/input.json"},
        "outputs": {"test_result_ref": "object-storage://evidence/RUN-20260702-001/result.json"},
        "state_before": {
            "snapshot_ref": "object-storage://evidence/RUN-20260702-001/state-before.json"
        },
        "state_after": {
            "snapshot_ref": "object-storage://evidence/RUN-20260702-001/state-after.json"
        },
        "state_diff": {
            "ref": "object-storage://evidence/RUN-20260702-001/state-diff.json",
            "summary": {"orders_changed": 1, "events_emitted": 1},
        },
        "tool_calls": [
            {
                "name": "pytest",
                "status": "success",
                "args_ref": "object-storage://evidence/RUN-20260702-001/tool-args.json",
            }
        ],
        "logs": [
            {
                "ref": "object-storage://evidence/RUN-20260702-001/test-runner.log",
                "kind": "test_runner",
            }
        ],
        "screenshots": [
            {
                "ref": "object-storage://evidence/RUN-20260702-001/order-cancel.png",
                "kind": "ui",
            }
        ],
        "grader_results": [
            {
                "verdict": "pass",
                "score": 1.0,
                "rationale_ref": "object-storage://evidence/RUN-20260702-001/grader.json",
                "confidence": 0.95,
            }
        ],
        "verdict": "pass",
        "reproduction_bundle": "object-storage://evidence/RUN-20260702-001/repro.zip",
    }


class TestSchemaItself:
    def test_schema_file_exists(self) -> None:
        assert (SCHEMAS_DIR / SCHEMA_FILENAME).is_file()

    def test_schema_is_valid_against_draft_2020_12_metaschema(self) -> None:
        Draft202012Validator.check_schema(load_schema(SCHEMA_FILENAME))

    def test_schema_declares_draft_2020_12(self) -> None:
        schema = load_schema(SCHEMA_FILENAME)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_inherits_artifact_base_via_allof(self) -> None:
        schema = load_schema(SCHEMA_FILENAME)
        assert {"$ref": "artifact-base.schema.json"} in schema.get("allOf", [])

    def test_artifact_type_is_fixed_by_const(self) -> None:
        schema = load_schema(SCHEMA_FILENAME)
        assert schema["properties"]["artifact_type"]["const"] == ARTIFACT_TYPE

    def test_required_matches_domain_required(self) -> None:
        schema = load_schema(SCHEMA_FILENAME)
        assert set(schema["required"]) == DOMAIN_REQUIRED_FIELDS | {"artifact_type"}

    def test_all_domain_required_fields_have_property_definitions(self) -> None:
        schema = load_schema(SCHEMA_FILENAME)
        missing = DOMAIN_REQUIRED_FIELDS - set(schema["properties"])
        assert not missing, f"required だが properties 未定義のfield: {missing}"


class TestValidInstances:
    def test_full_sample_passes(self) -> None:
        validator_for(SCHEMA_FILENAME).validate(make_valid_instance())

    def test_empty_collections_from_section_6_23_pass(self) -> None:
        instance = {
            **make_valid_instance(),
            "tool_calls": [],
            "logs": [],
            "screenshots": [],
            "grader_results": [],
        }
        validator_for(SCHEMA_FILENAME).validate(instance)

    def test_schema_embedded_examples_pass(self) -> None:
        examples = load_schema(SCHEMA_FILENAME).get("examples", [])
        assert examples, "examplesがキー欠落または空 — 空反復での素通り(vacuous pass)を防ぐ"
        validator = validator_for(SCHEMA_FILENAME)
        for example in examples:
            validator.validate(example)


class TestArtifactBaseInheritance:
    @pytest.mark.parametrize("base_field", sorted(SECTION_6_1_REQUIRED_FIELDS))
    def test_missing_base_required_field_fails(self, base_field: str) -> None:
        instance = {k: v for k, v in make_valid_instance().items() if k != base_field}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)

    def test_wrong_artifact_type_fails(self) -> None:
        instance = {**make_valid_instance(), "artifact_type": "something_else"}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)

    def test_unknown_field_fails(self) -> None:
        instance = {**make_valid_instance(), "unexpected_field": "typo"}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)


class TestDomainRequiredMissing:
    @pytest.mark.parametrize("missing", sorted(DOMAIN_REQUIRED_FIELDS))
    def test_missing_domain_required_field_fails(self, missing: str) -> None:
        instance = {k: v for k, v in make_valid_instance().items() if k != missing}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)


class TestExecutionEvidenceValues:
    @pytest.mark.parametrize("verdict", ["pass", "fail", "inconclusive"])
    def test_all_section_6_23_verdicts_pass(self, verdict: str) -> None:
        validator_for(SCHEMA_FILENAME).validate({**make_valid_instance(), "verdict": verdict})

    def test_unknown_verdict_fails(self) -> None:
        instance = {**make_valid_instance(), "verdict": "blocked"}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)

    def test_environment_requires_env_id(self) -> None:
        instance = {**make_valid_instance(), "environment": {"seed": "fixture-v1"}}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)

    @pytest.mark.parametrize("object_field", ["inputs", "outputs", "state_diff"])
    def test_evidence_payload_fields_must_be_objects(self, object_field: str) -> None:
        instance = {**make_valid_instance(), object_field: "object-storage://evidence/raw"}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)

    def test_log_entry_requires_ref(self) -> None:
        instance = {**make_valid_instance(), "logs": [{"kind": "app"}]}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)

    def test_grader_result_requires_verdict(self) -> None:
        instance = {**make_valid_instance(), "grader_results": [{"score": 1.0}]}
        with pytest.raises(ValidationError):
            validator_for(SCHEMA_FILENAME).validate(instance)

    def test_log_entry_preserves_extra_fields(self) -> None:
        instance = make_valid_instance()
        instance["logs"] = [
            {
                "ref": "object-storage://evidence/RUN-20260702-001/app.log",
                "kind": "app",
                "redaction_policy": "secrets-and-pii-redacted",
            }
        ]
        validator_for(SCHEMA_FILENAME).validate(instance)


class TestGeneratedModels:
    def _model_class(self) -> type:
        import importlib

        from gen_models import module_name_for

        module_name = module_name_for(SCHEMA_FILENAME).removesuffix(".py")
        module = importlib.import_module(f"models.{module_name}")
        return getattr(module, TITLE)

    def test_generated_model_accepts_schema_example(self) -> None:
        example = load_schema(SCHEMA_FILENAME)["examples"][0]
        model = self._model_class()(**example)
        assert model.artifact_type == ARTIFACT_TYPE or (
            getattr(model.artifact_type, "value", None) == ARTIFACT_TYPE
        )

    def test_generated_log_model_preserves_extra_fields(self) -> None:
        example = load_schema(SCHEMA_FILENAME)["examples"][0]
        model = self._model_class()(**example)
        dumped = model.model_dump()
        assert dumped["logs"][0].get("redaction_policy") == "secrets-and-pii-redacted"
