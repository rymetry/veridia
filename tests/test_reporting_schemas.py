"""QualityAnalyticsSnapshot / ReleaseReadinessReport schemaの契約テスト。

T-007 DoD:
- 各schemaが存在し、`allOf` で artifact-base を継承している
- QualityAnalyticsSnapshotがcoverage / execution / evidence / costを集約できる
- ReleaseReadinessReportがpass/warn/block・理由・evidence_refsを表現できる
- 有効サンプルがpassし、不正サンプルがfailする

North Star参照: §6.17(QualityAnalyticsSnapshot)、§6.18(ReleaseReadinessReport)、§6.1(共通contract)。
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

QUALITY_ANALYTICS_SNAPSHOT_SCHEMA = "quality-analytics-snapshot.schema.json"
RELEASE_READINESS_REPORT_SCHEMA = "release-readiness-report.schema.json"

QUALITY_ANALYTICS_SNAPSHOT_TITLE = "QualityAnalyticsSnapshot"
RELEASE_READINESS_REPORT_TITLE = "ReleaseReadinessReport"

QUALITY_ANALYTICS_SNAPSHOT_TYPE = "quality_analytics_snapshot"
RELEASE_READINESS_REPORT_TYPE = "release_readiness_report"

QUALITY_ANALYTICS_SNAPSHOT_REQUIRED_FIELDS = frozenset(
    {"snapshot_id", "scope", "coverage", "execution", "evidence", "cost"}
)
RELEASE_READINESS_REPORT_REQUIRED_FIELDS = frozenset(
    {
        "report_id",
        "release_candidate",
        "decision_recommendation",
        "blocking_reasons",
        "warning_reasons",
        "evidence_refs",
    }
)


def make_quality_analytics_snapshot_instance() -> dict[str, Any]:
    """§6.17のfield構成を満たす有効なQualityAnalyticsSnapshot instance。"""
    return {
        **make_base_fields(QUALITY_ANALYTICS_SNAPSHOT_TYPE),
        "artifact_id": "ART-QAS-001",
        "source_refs": ["SRC-PR-123", "SRC-CI-456"],
        "created_by": {
            "agent": "quality-analytics-agent",
            "skill": "quality-analytics-snapshot",
            "model": "claude-fable-5",
        },
        "confidence": 0.86,
        "snapshot_id": "QAS-20260630-001",
        "scope": {
            "release_candidate": "order-service@abc123",
            "branch": "release/2026-06-30",
            "time_window": {
                "from": "2026-06-29T00:00:00+09:00",
                "to": "2026-06-30T18:00:00+09:00",
            },
        },
        "coverage": {
            "requirement_coverage": 0.92,
            "risk_coverage": 0.88,
            "oracle_definition_rate": 0.97,
            "evidence_completeness": 0.95,
        },
        "execution": {
            "total_tests": 1240,
            "selected_tests": 312,
            "passed": 295,
            "failed": 9,
            "inconclusive": 8,
            "flaky_suspected": 5,
        },
        "quality_intelligence": {
            "impacted_requirements": 18,
            "coverage_gaps": 4,
            "untested_changes": 2,
            "high_risk_untested_changes": 1,
        },
        "evidence": {
            "evidence_refs": ["RUN-001", "RUN-002"],
            "evidence_count": 2,
            "missing_evidence_count": 0,
        },
        "cost": {
            "llm_cost_usd": 42.3,
            "test_runtime_minutes": 186,
            "cost_per_detected_defect": 14.1,
        },
    }


def make_release_readiness_report_instance() -> dict[str, Any]:
    """§6.18のfield構成を満たす有効なReleaseReadinessReport instance。"""
    return {
        **make_base_fields(RELEASE_READINESS_REPORT_TYPE),
        "artifact_id": "ART-RRR-001",
        "source_refs": ["SRC-PR-123"],
        "created_by": {
            "agent": "release-gate-agent",
            "skill": "release-readiness-reporting",
            "model": "claude-fable-5",
        },
        "confidence": 0.82,
        "report_id": "RRR-20260630-001",
        "release_candidate": "order-service@abc123",
        "decision_recommendation": "warn",
        "readiness_score": 0.82,
        "blocking_reasons": [],
        "warning_reasons": [
            {
                "reason": "high risk requirement has partial evidence",
                "requirement_ref": "REQ-BILLING-021",
                "risk_ref": "RISK-BILLING-004",
                "evidence_refs": ["RUN-20260630-014"],
            }
        ],
        "coverage_summary": {
            "p0_p1_source_grounding": 1.0,
            "p0_p1_oracle_definition": 1.0,
            "risk_coverage": 0.88,
            "evidence_completeness": 0.95,
        },
        "quality_intelligence_summary": {
            "untested_changes": 2,
            "coverage_gaps": 4,
            "recommended_followups": [
                "add API regression for billing cancellation edge case",
                "review skipped UI test for admin refund flow",
            ],
        },
        "human_review_required": True,
        "required_approvers": ["qa_lead", "billing_owner"],
        "analytics_snapshot_ref": "QAS-20260630-001",
        "residual_risk_report_ref": "RRISK-REL-20260630-001",
        "evidence_refs": ["RUN-20260630-014", "QAS-20260630-001"],
    }


@pytest.mark.parametrize(
    ("schema_filename", "artifact_type", "domain_required"),
    [
        (
            QUALITY_ANALYTICS_SNAPSHOT_SCHEMA,
            QUALITY_ANALYTICS_SNAPSHOT_TYPE,
            QUALITY_ANALYTICS_SNAPSHOT_REQUIRED_FIELDS,
        ),
        (
            RELEASE_READINESS_REPORT_SCHEMA,
            RELEASE_READINESS_REPORT_TYPE,
            RELEASE_READINESS_REPORT_REQUIRED_FIELDS,
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
    def test_quality_analytics_snapshot_full_sample_passes(self) -> None:
        validator_for(QUALITY_ANALYTICS_SNAPSHOT_SCHEMA).validate(
            make_quality_analytics_snapshot_instance()
        )

    def test_quality_analytics_snapshot_unmeasured_optional_metrics_pass(self) -> None:
        instance = make_quality_analytics_snapshot_instance()
        instance["coverage"] = {}
        instance["execution"] = {}
        instance["evidence"] = {"evidence_refs": [], "evidence_count": 0}
        instance["cost"] = {}
        validator_for(QUALITY_ANALYTICS_SNAPSHOT_SCHEMA).validate(instance)

    def test_release_readiness_report_warn_sample_passes(self) -> None:
        validator_for(RELEASE_READINESS_REPORT_SCHEMA).validate(
            make_release_readiness_report_instance()
        )

    @pytest.mark.parametrize("decision", ["pass", "warn", "block"])
    def test_release_readiness_report_all_decisions_pass(self, decision: str) -> None:
        instance = {
            **make_release_readiness_report_instance(),
            "decision_recommendation": decision,
        }
        validator_for(RELEASE_READINESS_REPORT_SCHEMA).validate(instance)

    @pytest.mark.parametrize(
        "schema_filename",
        [QUALITY_ANALYTICS_SNAPSHOT_SCHEMA, RELEASE_READINESS_REPORT_SCHEMA],
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
        (QUALITY_ANALYTICS_SNAPSHOT_SCHEMA, make_quality_analytics_snapshot_instance),
        (RELEASE_READINESS_REPORT_SCHEMA, make_release_readiness_report_instance),
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

    def test_empty_source_refs_fails(self, schema_filename: str, make_instance: Any) -> None:
        instance = {**make_instance(), "source_refs": []}
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
            QUALITY_ANALYTICS_SNAPSHOT_SCHEMA,
            make_quality_analytics_snapshot_instance,
            QUALITY_ANALYTICS_SNAPSHOT_REQUIRED_FIELDS,
        ),
        (
            RELEASE_READINESS_REPORT_SCHEMA,
            make_release_readiness_report_instance,
            RELEASE_READINESS_REPORT_REQUIRED_FIELDS,
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


class TestQualityAnalyticsSnapshotValues:
    def test_coverage_metric_must_be_between_zero_and_one(self) -> None:
        instance = make_quality_analytics_snapshot_instance()
        instance["coverage"]["requirement_coverage"] = 1.2
        with pytest.raises(ValidationError):
            validator_for(QUALITY_ANALYTICS_SNAPSHOT_SCHEMA).validate(instance)

    def test_execution_counts_must_be_non_negative(self) -> None:
        instance = make_quality_analytics_snapshot_instance()
        instance["execution"]["failed"] = -1
        with pytest.raises(ValidationError):
            validator_for(QUALITY_ANALYTICS_SNAPSHOT_SCHEMA).validate(instance)

    def test_evidence_refs_must_be_array(self) -> None:
        instance = make_quality_analytics_snapshot_instance()
        instance["evidence"]["evidence_refs"] = "RUN-001"
        with pytest.raises(ValidationError):
            validator_for(QUALITY_ANALYTICS_SNAPSHOT_SCHEMA).validate(instance)

    def test_cost_values_must_be_non_negative(self) -> None:
        instance = make_quality_analytics_snapshot_instance()
        instance["cost"]["llm_cost_usd"] = -0.1
        with pytest.raises(ValidationError):
            validator_for(QUALITY_ANALYTICS_SNAPSHOT_SCHEMA).validate(instance)


class TestReleaseReadinessReportValues:
    def test_unknown_decision_recommendation_fails(self) -> None:
        instance = {
            **make_release_readiness_report_instance(),
            "decision_recommendation": "defer",
        }
        with pytest.raises(ValidationError):
            validator_for(RELEASE_READINESS_REPORT_SCHEMA).validate(instance)

    def test_readiness_score_must_be_between_zero_and_one(self) -> None:
        instance = {**make_release_readiness_report_instance(), "readiness_score": 1.2}
        with pytest.raises(ValidationError):
            validator_for(RELEASE_READINESS_REPORT_SCHEMA).validate(instance)

    def test_reason_requires_reason_text(self) -> None:
        instance = make_release_readiness_report_instance()
        instance["warning_reasons"] = [{"evidence_refs": ["RUN-001"]}]
        with pytest.raises(ValidationError):
            validator_for(RELEASE_READINESS_REPORT_SCHEMA).validate(instance)

    def test_evidence_refs_must_be_strings(self) -> None:
        instance = {**make_release_readiness_report_instance(), "evidence_refs": [123]}
        with pytest.raises(ValidationError):
            validator_for(RELEASE_READINESS_REPORT_SCHEMA).validate(instance)


@pytest.mark.parametrize(
    ("schema_filename", "title", "artifact_type"),
    [
        (
            QUALITY_ANALYTICS_SNAPSHOT_SCHEMA,
            QUALITY_ANALYTICS_SNAPSHOT_TITLE,
            QUALITY_ANALYTICS_SNAPSHOT_TYPE,
        ),
        (
            RELEASE_READINESS_REPORT_SCHEMA,
            RELEASE_READINESS_REPORT_TITLE,
            RELEASE_READINESS_REPORT_TYPE,
        ),
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
