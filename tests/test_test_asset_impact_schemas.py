"""TestAssetIndex / ChangeImpactSpec schemaの契約テスト。

T-006 DoD:
- 各schemaが存在し、`allOf` で artifact-base を継承している
- TestAssetIndexが既存テストのpath / type / covered requirement・risk /
  oracle / flake rateを保持できる
- ChangeImpactSpecが影響component / requirement / risk / APIを保持できる
- 有効サンプルがpassし、不正サンプルがfailする

North Star参照: §6.13(TestAssetIndex)、§6.9(ChangeImpactSpec)、§21 Week 1。
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

TEST_ASSET_INDEX_SCHEMA = "test-asset-index.schema.json"
CHANGE_IMPACT_SPEC_SCHEMA = "change-impact-spec.schema.json"

TEST_ASSET_INDEX_TYPE = "test_asset_index"
CHANGE_IMPACT_SPEC_TYPE = "change_impact_spec"

TEST_ASSET_INDEX_REQUIRED_FIELDS = frozenset({"index_id", "indexed_at", "scope", "assets"})
CHANGE_IMPACT_SPEC_REQUIRED_FIELDS = frozenset(
    {
        "change_impact_id",
        "changed_files",
        "changed_components",
        "impacted_requirements",
        "impacted_risks",
        "impacted_apis",
    }
)

TEST_TYPES = (
    "unit",
    "integration",
    "api",
    "e2e",
    "ui",
    "contract",
    "performance",
    "security",
    "manual",
    "other",
)
CHANGE_TYPES = ("added", "modified", "deleted", "renamed")
RISK_LEVELS = ("low", "medium", "high", "critical")


def make_test_asset_index_instance() -> dict[str, Any]:
    """§6.13のサンプル相当の有効なTestAssetIndex instance。"""
    return {
        **make_base_fields(TEST_ASSET_INDEX_TYPE),
        "artifact_id": "ART-TAI-001",
        "source_refs": ["internal://github/org/repo/tree/main"],
        "created_by": {
            "agent": "test-asset-agent",
            "skill": "existing-test-discovery",
            "model": "claude-fable-5",
        },
        "confidence": 0.83,
        "index_id": "TAI-ORDER-001",
        "indexed_at": "2026-06-30T12:00:00+09:00",
        "scope": {
            "repository": "order-service",
            "branch": "main",
        },
        "assets": [
            {
                "test_id": "TEST-API-ORDER-CANCEL-001",
                "test_type": "api",
                "path": "tests/api/order_cancel.test.ts",
                "covered_requirements": ["REQ-ORDER-CANCEL-001"],
                "covered_risks": ["RISK-BILLING-001"],
                "covered_apis": ["POST /orders/{id}/cancel"],
                "covered_state_models": ["STATE-ORDER-001"],
                "oracle_refs": ["ORACLE-ORDER-CANCEL-001"],
                "stability": {
                    "flake_rate": 0.01,
                    "last_failed_at": None,
                    "last_passed_at": "2026-06-30T10:00:00+09:00",
                },
                "maintenance": {
                    "owner": "order-team",
                    "last_modified": "2026-06-20",
                    "maintenance_cost": "low",
                },
            }
        ],
    }


def make_change_impact_spec_instance() -> dict[str, Any]:
    """§6.9のサンプル相当の有効なChangeImpactSpec instance。"""
    return {
        **make_base_fields(CHANGE_IMPACT_SPEC_TYPE),
        "artifact_id": "ART-CIS-001",
        "source_refs": ["SRC-PR-123"],
        "created_by": {
            "agent": "quality-intelligence-agent",
            "skill": "change-impact-analysis",
            "model": "claude-fable-5",
        },
        "confidence": 0.84,
        "change_impact_id": "CIS-PR-123",
        "changed_files": [
            {
                "path": "src/order/cancel_order.ts",
                "change_type": "modified",
                "risk_level": "high",
            }
        ],
        "changed_components": ["order-service", "payment-adapter"],
        "impacted_requirements": ["REQ-ORDER-CANCEL-001", "REQ-BILLING-VOID-002"],
        "impacted_risks": ["RISK-BILLING-001", "RISK-AUDIT-003"],
        "impacted_apis": ["POST /orders/{id}/cancel", "GET /orders/{id}"],
        "impacted_state_models": ["STATE-ORDER-001"],
        "impacted_existing_tests": ["TEST-API-ORDER-CANCEL-001"],
    }


@pytest.mark.parametrize(
    ("schema_filename", "artifact_type", "domain_required"),
    [
        (TEST_ASSET_INDEX_SCHEMA, TEST_ASSET_INDEX_TYPE, TEST_ASSET_INDEX_REQUIRED_FIELDS),
        (
            CHANGE_IMPACT_SPEC_SCHEMA,
            CHANGE_IMPACT_SPEC_TYPE,
            CHANGE_IMPACT_SPEC_REQUIRED_FIELDS,
        ),
    ],
)
class TestSchemaItself:
    def test_schema_file_exists(
        self, schema_filename: str, artifact_type: str, domain_required: frozenset[str]
    ) -> None:
        _ = (artifact_type, domain_required)
        assert (SCHEMAS_DIR / schema_filename).is_file(), (
            f"schema正本が存在しない: {schema_filename}"
        )

    def test_schema_is_valid_against_draft_2020_12_metaschema(
        self, schema_filename: str, artifact_type: str, domain_required: frozenset[str]
    ) -> None:
        _ = (artifact_type, domain_required)
        Draft202012Validator.check_schema(load_schema(schema_filename))

    def test_schema_declares_draft_2020_12(
        self, schema_filename: str, artifact_type: str, domain_required: frozenset[str]
    ) -> None:
        _ = (artifact_type, domain_required)
        schema = load_schema(schema_filename)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_inherits_artifact_base_via_allof(
        self, schema_filename: str, artifact_type: str, domain_required: frozenset[str]
    ) -> None:
        _ = (artifact_type, domain_required)
        schema = load_schema(schema_filename)
        assert {"$ref": "artifact-base.schema.json"} in schema.get("allOf", [])

    def test_artifact_type_is_fixed_by_const(
        self, schema_filename: str, artifact_type: str, domain_required: frozenset[str]
    ) -> None:
        _ = domain_required
        schema = load_schema(schema_filename)
        assert schema["properties"]["artifact_type"]["const"] == artifact_type

    def test_required_matches_domain_required(
        self,
        schema_filename: str,
        artifact_type: str,
        domain_required: frozenset[str],
    ) -> None:
        _ = artifact_type
        schema = load_schema(schema_filename)
        assert set(schema["required"]) == domain_required | {"artifact_type"}

    def test_all_domain_required_fields_have_property_definitions(
        self,
        schema_filename: str,
        artifact_type: str,
        domain_required: frozenset[str],
    ) -> None:
        _ = artifact_type
        schema = load_schema(schema_filename)
        missing = domain_required - set(schema["properties"])
        assert not missing, f"required だが properties 未定義のfield: {missing}"


class TestValidInstances:
    def test_test_asset_index_full_sample_passes(self) -> None:
        validator_for(TEST_ASSET_INDEX_SCHEMA).validate(make_test_asset_index_instance())

    def test_test_asset_index_phase_0_generator_sample_passes(self) -> None:
        instance = make_test_asset_index_instance()
        asset = instance["assets"][0]
        asset["covered_requirements"] = []
        asset["covered_risks"] = []
        asset["oracle_refs"] = []
        asset["stability"]["flake_rate"] = None
        validator_for(TEST_ASSET_INDEX_SCHEMA).validate(instance)

    def test_change_impact_spec_full_sample_passes(self) -> None:
        validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(make_change_impact_spec_instance())

    def test_change_impact_spec_phase_0_candidate_sample_passes(self) -> None:
        instance = {
            **make_change_impact_spec_instance(),
            "impacted_requirements": [],
            "impacted_risks": [],
            "impacted_apis": [],
        }
        validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(instance)

    @pytest.mark.parametrize(
        "schema_filename", [TEST_ASSET_INDEX_SCHEMA, CHANGE_IMPACT_SPEC_SCHEMA]
    )
    def test_schema_embedded_examples_pass(self, schema_filename: str) -> None:
        examples = load_schema(schema_filename).get("examples", [])
        assert examples, "examplesがキー欠落または空 — 空反復での素通り(vacuous pass)を防ぐ"
        validator = validator_for(schema_filename)
        for example in examples:
            validator.validate(example)


@pytest.mark.parametrize(
    ("schema_filename", "make_instance"),
    [
        (TEST_ASSET_INDEX_SCHEMA, make_test_asset_index_instance),
        (CHANGE_IMPACT_SPEC_SCHEMA, make_change_impact_spec_instance),
    ],
)
class TestArtifactBaseInheritance:
    @pytest.mark.parametrize("base_field", sorted(SECTION_6_1_REQUIRED_FIELDS))
    def test_missing_base_required_field_fails(
        self, schema_filename: str, make_instance: Any, base_field: str
    ) -> None:
        instance = {k: v for k, v in make_instance().items() if k != base_field}
        with pytest.raises(ValidationError):
            validator_for(schema_filename).validate(instance)

    def test_wrong_artifact_type_fails(self, schema_filename: str, make_instance: Any) -> None:
        instance = {**make_instance(), "artifact_type": "something_else"}
        with pytest.raises(ValidationError):
            validator_for(schema_filename).validate(instance)

    def test_unknown_top_level_field_fails(self, schema_filename: str, make_instance: Any) -> None:
        instance = {**make_instance(), "unexpected_field": "typo"}
        with pytest.raises(ValidationError):
            validator_for(schema_filename).validate(instance)


@pytest.mark.parametrize(
    ("schema_filename", "make_instance", "domain_required"),
    [
        (
            TEST_ASSET_INDEX_SCHEMA,
            make_test_asset_index_instance,
            TEST_ASSET_INDEX_REQUIRED_FIELDS,
        ),
        (
            CHANGE_IMPACT_SPEC_SCHEMA,
            make_change_impact_spec_instance,
            CHANGE_IMPACT_SPEC_REQUIRED_FIELDS,
        ),
    ],
)
class TestDomainRequiredMissing:
    def test_missing_domain_required_field_fails(
        self, schema_filename: str, make_instance: Any, domain_required: frozenset[str]
    ) -> None:
        for missing in domain_required:
            instance = {k: v for k, v in make_instance().items() if k != missing}
            with pytest.raises(ValidationError):
                validator_for(schema_filename).validate(instance)


class TestTestAssetIndexValues:
    @pytest.mark.parametrize("test_type", TEST_TYPES)
    def test_all_test_types_pass(self, test_type: str) -> None:
        instance = make_test_asset_index_instance()
        instance["assets"][0]["test_type"] = test_type
        validator_for(TEST_ASSET_INDEX_SCHEMA).validate(instance)

    def test_unknown_test_type_fails(self) -> None:
        instance = make_test_asset_index_instance()
        instance["assets"][0]["test_type"] = "chaos"
        with pytest.raises(ValidationError):
            validator_for(TEST_ASSET_INDEX_SCHEMA).validate(instance)

    def test_asset_requires_path(self) -> None:
        instance = make_test_asset_index_instance()
        del instance["assets"][0]["path"]
        with pytest.raises(ValidationError):
            validator_for(TEST_ASSET_INDEX_SCHEMA).validate(instance)

    def test_asset_requires_oracle_refs(self) -> None:
        instance = make_test_asset_index_instance()
        del instance["assets"][0]["oracle_refs"]
        with pytest.raises(ValidationError):
            validator_for(TEST_ASSET_INDEX_SCHEMA).validate(instance)

    def test_flake_rate_must_be_between_zero_and_one(self) -> None:
        instance = make_test_asset_index_instance()
        instance["assets"][0]["stability"]["flake_rate"] = 1.2
        with pytest.raises(ValidationError):
            validator_for(TEST_ASSET_INDEX_SCHEMA).validate(instance)

    def test_asset_metadata_extra_fields_pass(self) -> None:
        instance = make_test_asset_index_instance()
        instance["assets"][0]["runner"] = "pytest"
        validator_for(TEST_ASSET_INDEX_SCHEMA).validate(instance)


class TestChangeImpactSpecValues:
    @pytest.mark.parametrize("change_type", CHANGE_TYPES)
    def test_all_change_types_pass(self, change_type: str) -> None:
        instance = make_change_impact_spec_instance()
        instance["changed_files"][0]["change_type"] = change_type
        validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(instance)

    def test_unknown_change_type_fails(self) -> None:
        instance = make_change_impact_spec_instance()
        instance["changed_files"][0]["change_type"] = "rewritten"
        with pytest.raises(ValidationError):
            validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(instance)

    @pytest.mark.parametrize("risk_level", RISK_LEVELS)
    def test_all_changed_file_risk_levels_pass(self, risk_level: str) -> None:
        instance = make_change_impact_spec_instance()
        instance["changed_files"][0]["risk_level"] = risk_level
        validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(instance)

    def test_changed_file_requires_path(self) -> None:
        instance = make_change_impact_spec_instance()
        del instance["changed_files"][0]["path"]
        with pytest.raises(ValidationError):
            validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(instance)

    def test_impacted_apis_must_be_strings(self) -> None:
        instance = {**make_change_impact_spec_instance(), "impacted_apis": [123]}
        with pytest.raises(ValidationError):
            validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(instance)

    def test_empty_changed_components_fails(self) -> None:
        instance = {**make_change_impact_spec_instance(), "changed_components": []}
        with pytest.raises(ValidationError):
            validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(instance)

    def test_changed_file_extra_fields_pass(self) -> None:
        instance = make_change_impact_spec_instance()
        instance["changed_files"][0]["lines_changed"] = 42
        validator_for(CHANGE_IMPACT_SPEC_SCHEMA).validate(instance)


@pytest.mark.parametrize(
    ("schema_filename", "title", "artifact_type"),
    [
        (TEST_ASSET_INDEX_SCHEMA, "TestAssetIndex", TEST_ASSET_INDEX_TYPE),
        (CHANGE_IMPACT_SPEC_SCHEMA, "ChangeImpactSpec", CHANGE_IMPACT_SPEC_TYPE),
    ],
)
class TestGeneratedModels:
    def _model_class(self, schema_filename: str, title: str) -> type:
        import importlib

        from gen_models import module_name_for

        module_name = module_name_for(schema_filename).removesuffix(".py")
        module = importlib.import_module(f"models.{module_name}")
        return getattr(module, title)

    def test_generated_model_accepts_schema_example(
        self, schema_filename: str, title: str, artifact_type: str
    ) -> None:
        example = load_schema(schema_filename)["examples"][0]
        model = self._model_class(schema_filename, title)(**example)
        assert model.artifact_type == artifact_type or (
            getattr(model.artifact_type, "value", None) == artifact_type
        )

    def test_generated_model_rejects_missing_domain_field(
        self, schema_filename: str, title: str, artifact_type: str
    ) -> None:
        _ = artifact_type
        from pydantic import ValidationError as PydanticValidationError

        required = set(load_schema(schema_filename)["required"]) - {"artifact_type"}
        first_required = sorted(required)[0]
        example = load_schema(schema_filename)["examples"][0]
        broken = {k: v for k, v in example.items() if k != first_required}
        with pytest.raises(PydanticValidationError):
            self._model_class(schema_filename, title)(**broken)
