"""コアspec schema(requirement-spec / risk-spec / oracle-spec)の契約テスト。

T-004 DoD:
- 各schemaが存在し、`allOf` で artifact-base を継承している
- 有効サンプルがpassし、domain固有必須field欠落サンプルがfailする

North Star参照: §6.3(RequirementSpec)、§6.4(RiskSpec)、§6.6(OracleSpec)、
§9.2/§9.3(oracle分類 = oracle_typeの値域)、§9.1(oracle-first: OracleSpecは要求ごと)。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource

from tests.test_artifact_base_schema import SECTION_6_1_REQUIRED_FIELDS

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

# §9.2 Oracle分類 + §9.3 Oracle優先順位(model judge)に列挙された全oracle種別
ORACLE_TYPES = (
    "exact",
    "state",
    "contract",
    "invariant",
    "differential",
    "metamorphic",
    "statistical",
    "model_judge",
    "human",
)

# severity / business_impact の値域(North Starの用例: §6.4 critical、§6.3 high、§8.4)
FOUR_LEVEL_SCALE = ("low", "medium", "high", "critical")
# likelihood / detectability の値域(発生しやすさ・検出しやすさに criticalは意味を成さない)
THREE_LEVEL_SCALE = ("low", "medium", "high")


@dataclass(frozen=True)
class SpecCase:
    """スキーマ1件分の期待契約(テストのパラメータ)。"""

    schema_filename: str
    title: str
    artifact_type: str
    domain_required: frozenset[str]
    domain_fields: dict[str, Any] = field(hash=False)


SPEC_CASES = (
    SpecCase(
        schema_filename="requirement-spec.schema.json",
        title="RequirementSpec",
        artifact_type="requirement_spec",
        domain_required=frozenset({"req_id", "title", "acceptance_criteria"}),
        domain_fields={
            "req_id": "REQ-ORDER-CANCEL-001",
            "title": "支払い承認済み注文をキャンセルできる",
            "description": "ユーザーは条件を満たす注文をキャンセルできる",
            "acceptance_criteria": [
                "注文状態がCANCELLEDになる",
                "在庫が戻る",
                "決済がvoid/refundされる",
                "監査ログが記録される",
            ],
            "business_impact": "high",
            "owner": "order-team",
        },
    ),
    SpecCase(
        schema_filename="risk-spec.schema.json",
        title="RiskSpec",
        artifact_type="risk_spec",
        domain_required=frozenset({"risk_id", "title", "severity", "likelihood"}),
        domain_fields={
            "risk_id": "RISK-BILLING-001",
            "title": "キャンセル時の誤請求",
            "severity": "critical",
            "likelihood": "medium",
            "detectability": "medium",
            "risk_type": "financial",
            "past_incident_refs": ["INC-2026-014"],
            "mitigation": "State oracle + payment mock + event verification",
        },
    ),
    SpecCase(
        schema_filename="oracle-spec.schema.json",
        title="OracleSpec",
        artifact_type="oracle_spec",
        domain_required=frozenset(
            {"oracle_id", "req_refs", "oracle_type", "signals", "pass_condition"}
        ),
        domain_fields={
            "oracle_id": "ORACLE-ORDER-CANCEL-001",
            "req_refs": ["REQ-ORDER-CANCEL-001"],
            "risk_refs": ["RISK-BILLING-001"],
            "oracle_type": ["state", "invariant", "contract"],
            "signals": [
                {"type": "db", "query_ref": "order_status_check"},
                {"type": "api", "endpoint": "GET /orders/{id}"},
                {"type": "event", "topic": "order.cancelled"},
                {"type": "audit_log", "event": "ORDER_CANCELLED"},
            ],
            "pass_condition": "all required state changes observed",
            "human_review_required_if": [
                "payment_result ambiguous",
                "state_diff incomplete",
            ],
        },
    ),
)

CASE_IDS = [case.title for case in SPEC_CASES]

# (case, domain必須field) の全組み合わせ(欠落テスト用)
DOMAIN_REQUIRED_PAIRS = [
    pytest.param(case, missing, id=f"{case.title}-{missing}")
    for case in SPEC_CASES
    for missing in sorted(case.domain_required)
]


def load_schema(filename: str) -> dict[str, Any]:
    return json.loads((SCHEMAS_DIR / filename).read_text(encoding="utf-8"))


@cache
def build_registry() -> Registry:
    """schemas/ 配下の全schemaを $id で引けるregistry($refの解決に使う)。"""
    resources = [
        Resource.from_contents(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(SCHEMAS_DIR.glob("*.schema.json"))
    ]
    return Registry().with_resources((r.contents["$id"], r) for r in resources)


@cache
def validator_for(filename: str) -> Draft202012Validator:
    return Draft202012Validator(load_schema(filename), registry=build_registry())


def make_base_fields(artifact_type: str) -> dict[str, Any]:
    """§6.1の共通必須fieldを満たす部分instanceを毎回新しく作る(共有状態を持たない)。"""
    return {
        "artifact_id": "ART-001",
        "artifact_type": artifact_type,
        "version": "0.1.0",
        "source_refs": ["internal://github/org/repo/pull/123"],
        "created_by": {
            "agent": "qa-analyst",
            "skill": "requirement-extraction",
            "model": "claude-fable-5",
        },
        "confidence": 0.82,
        "status": "draft",
        "requires_human_review": True,
        "trace_id": "trace-20260702-0001",
        "created_at": "2026-07-02T10:00:00Z",
    }


def make_valid_instance(case: SpecCase) -> dict[str, Any]:
    """base全field + domain全field(optional含む)の有効instance。"""
    return {**make_base_fields(case.artifact_type), **case.domain_fields}


def make_minimal_instance(case: SpecCase) -> dict[str, Any]:
    """base全field + domain必須fieldのみの有効instance(optional欠落でも通ること)。"""
    domain = {k: v for k, v in case.domain_fields.items() if k in case.domain_required}
    return {**make_base_fields(case.artifact_type), **domain}


@pytest.mark.parametrize("case", SPEC_CASES, ids=CASE_IDS)
class TestSchemaItself:
    def test_schema_file_exists(self, case: SpecCase) -> None:
        path = SCHEMAS_DIR / case.schema_filename
        assert path.is_file(), f"schema正本が存在しない: {path}"

    def test_schema_is_valid_against_draft_2020_12_metaschema(self, case: SpecCase) -> None:
        Draft202012Validator.check_schema(load_schema(case.schema_filename))

    def test_schema_declares_draft_2020_12(self, case: SpecCase) -> None:
        schema = load_schema(case.schema_filename)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_inherits_artifact_base_via_allof(self, case: SpecCase) -> None:
        # DoD: allOf で artifact-base を継承する(schemas/README.md の規約)
        schema = load_schema(case.schema_filename)
        assert {"$ref": "artifact-base.schema.json"} in schema.get("allOf", [])

    def test_artifact_type_is_fixed_by_const(self, case: SpecCase) -> None:
        # §6.1: artifact_type は各schemaが const で自身の型名に固定する
        schema = load_schema(case.schema_filename)
        assert schema["properties"]["artifact_type"]["const"] == case.artifact_type

    def test_required_matches_domain_required(self, case: SpecCase) -> None:
        # T-001の学びへの守り: required と期待値の完全一致で静かな縮退を防ぐ。
        # artifact_typeはbase側でもrequiredだが、子で再宣言(const)したfieldをrequiredに
        # 含めないと生成PydanticモデルがOptional化して契約が緩むため、子側にも列挙する
        schema = load_schema(case.schema_filename)
        assert set(schema["required"]) == case.domain_required | {"artifact_type"}

    def test_all_domain_required_fields_have_property_definitions(self, case: SpecCase) -> None:
        schema = load_schema(case.schema_filename)
        missing = case.domain_required - set(schema["properties"])
        assert not missing, f"required だが properties 未定義のfield: {missing}"


@pytest.mark.parametrize("case", SPEC_CASES, ids=CASE_IDS)
class TestValidInstances:
    def test_full_sample_passes(self, case: SpecCase) -> None:
        validator_for(case.schema_filename).validate(make_valid_instance(case))

    def test_minimal_sample_passes(self, case: SpecCase) -> None:
        validator_for(case.schema_filename).validate(make_minimal_instance(case))

    def test_schema_embedded_examples_pass(self, case: SpecCase) -> None:
        examples = load_schema(case.schema_filename).get("examples", [])
        assert examples, "examplesがキー欠落または空 — 空反復での素通り(vacuous pass)を防ぐ"
        validator = validator_for(case.schema_filename)
        for example in examples:
            validator.validate(example)


@pytest.mark.parametrize("case", SPEC_CASES, ids=CASE_IDS)
class TestArtifactBaseInheritance:
    """base側の契約が allOf 継承を通して実際に強制されることの検証。"""

    @pytest.mark.parametrize("base_field", sorted(SECTION_6_1_REQUIRED_FIELDS))
    def test_missing_base_required_field_fails(self, case: SpecCase, base_field: str) -> None:
        instance = {k: v for k, v in make_valid_instance(case).items() if k != base_field}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_empty_source_refs_fails(self, case: SpecCase) -> None:
        # ADR-0002: source_refs は required + minItems: 1
        instance = {**make_valid_instance(case), "source_refs": []}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_wrong_artifact_type_fails(self, case: SpecCase) -> None:
        instance = {**make_valid_instance(case), "artifact_type": "something_else"}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_unknown_field_fails(self, case: SpecCase) -> None:
        # baseは合成のため開いているが、末端の具象schemaは unevaluatedProperties: false で
        # 閉じる(field名のtypo等の契約違反を境界でfail-fastさせる)
        instance = {**make_valid_instance(case), "unexpected_field": "typo"}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)


class TestDomainRequiredMissing:
    @pytest.mark.parametrize(("case", "missing"), DOMAIN_REQUIRED_PAIRS)
    def test_missing_domain_required_field_fails(self, case: SpecCase, missing: str) -> None:
        instance = {k: v for k, v in make_valid_instance(case).items() if k != missing}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)


def _case(title: str) -> SpecCase:
    return next(c for c in SPEC_CASES if c.title == title)


class TestRequirementSpecValues:
    def test_empty_acceptance_criteria_fails(self) -> None:
        case = _case("RequirementSpec")
        instance = {**make_valid_instance(case), "acceptance_criteria": []}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_non_string_acceptance_criteria_item_fails(self) -> None:
        case = _case("RequirementSpec")
        instance = {**make_valid_instance(case), "acceptance_criteria": [123]}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    @pytest.mark.parametrize("impact", FOUR_LEVEL_SCALE)
    def test_all_business_impact_values_pass(self, impact: str) -> None:
        case = _case("RequirementSpec")
        validator_for(case.schema_filename).validate(
            {**make_valid_instance(case), "business_impact": impact}
        )

    def test_unknown_business_impact_fails(self) -> None:
        case = _case("RequirementSpec")
        instance = {**make_valid_instance(case), "business_impact": "catastrophic"}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)


class TestRiskSpecValues:
    @pytest.mark.parametrize("severity", FOUR_LEVEL_SCALE)
    def test_all_severity_values_pass(self, severity: str) -> None:
        case = _case("RiskSpec")
        validator_for(case.schema_filename).validate(
            {**make_valid_instance(case), "severity": severity}
        )

    def test_unknown_severity_fails(self) -> None:
        case = _case("RiskSpec")
        instance = {**make_valid_instance(case), "severity": "blocker"}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    @pytest.mark.parametrize("scale_field", ["likelihood", "detectability"])
    @pytest.mark.parametrize("value", THREE_LEVEL_SCALE)
    def test_three_level_scale_values_pass(self, scale_field: str, value: str) -> None:
        case = _case("RiskSpec")
        validator_for(case.schema_filename).validate(
            {**make_valid_instance(case), scale_field: value}
        )

    @pytest.mark.parametrize("scale_field", ["likelihood", "detectability"])
    def test_critical_is_not_a_likelihood_or_detectability(self, scale_field: str) -> None:
        # severityと違い、発生しやすさ・検出しやすさの尺度に critical は含めない
        case = _case("RiskSpec")
        instance = {**make_valid_instance(case), scale_field: "critical"}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)


class TestOracleSpecValues:
    @pytest.mark.parametrize("oracle_type", ORACLE_TYPES)
    def test_all_section_9_oracle_types_pass(self, oracle_type: str) -> None:
        case = _case("OracleSpec")
        validator_for(case.schema_filename).validate(
            {**make_valid_instance(case), "oracle_type": [oracle_type]}
        )

    def test_unknown_oracle_type_fails(self) -> None:
        case = _case("OracleSpec")
        instance = {**make_valid_instance(case), "oracle_type": ["vibes"]}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_empty_oracle_type_fails(self) -> None:
        case = _case("OracleSpec")
        instance = {**make_valid_instance(case), "oracle_type": []}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_duplicate_oracle_type_fails(self) -> None:
        case = _case("OracleSpec")
        instance = {**make_valid_instance(case), "oracle_type": ["state", "state"]}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_empty_req_refs_fails(self) -> None:
        # §9.1 oracle-first: OracleSpecは要求ごとに作る → 参照先要求が最低1件必要
        case = _case("OracleSpec")
        instance = {**make_valid_instance(case), "req_refs": []}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_empty_signals_fails(self) -> None:
        case = _case("OracleSpec")
        instance = {**make_valid_instance(case), "signals": []}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_signal_without_type_fails(self) -> None:
        case = _case("OracleSpec")
        instance = {**make_valid_instance(case), "signals": [{"query_ref": "x"}]}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_signal_extra_fields_pass(self) -> None:
        # signalの形はtype毎に異なる(query_ref / endpoint / topic / event等)ため開いておく
        case = _case("OracleSpec")
        signal = {"type": "metric", "metric_name": "p99_latency", "threshold_ms": 500}
        validator_for(case.schema_filename).validate(
            {**make_valid_instance(case), "signals": [signal]}
        )

    def test_empty_optional_array_fails(self) -> None:
        # optional配列は「空にするならキー省略」の規約(minItems: 1)。空配列の曖昧さを防ぐ
        case = _case("OracleSpec")
        instance = {**make_valid_instance(case), "risk_refs": []}
        with pytest.raises(ValidationError):
            validator_for(case.schema_filename).validate(instance)

    def test_generated_model_does_not_enforce_unique_oracle_type(self) -> None:
        # uniqueItems(生JSONでは重複reject = test_duplicate_oracle_type_fails)は
        # dcgがPydantic制約へ変換しないため、生成モデルでは重複が通る。既知の非対称
        # として挙動を固定する(dcgが変換するようになったらこのテストが検知する)
        import importlib

        from gen_models import module_name_for

        case = _case("OracleSpec")
        module_name = module_name_for(case.schema_filename).removesuffix(".py")
        oracle_spec = importlib.import_module(f"models.{module_name}")
        example = load_schema(case.schema_filename)["examples"][0]
        model = oracle_spec.OracleSpec(**{**example, "oracle_type": ["state", "state"]})
        assert [t.value for t in model.oracle_type] == ["state", "state"]

    def test_generated_signal_model_preserves_extra_fields(self) -> None:
        # signalはtype毎に異なるfield(query_ref / endpoint / topic等)を持つ開いたobject。
        # 生成PydanticモデルがPydantic既定(extra=ignore)のままだとround-tripでsignalの
        # 中身が黙って消える(silent data loss)ため、extra=allowで保持されることを検証する
        import importlib

        from gen_models import module_name_for

        case = _case("OracleSpec")
        module_name = module_name_for(case.schema_filename).removesuffix(".py")
        oracle_spec = importlib.import_module(f"models.{module_name}")
        example = load_schema(case.schema_filename)["examples"][0]
        model = oracle_spec.OracleSpec(**example)
        dumped = model.model_dump()
        assert dumped["signals"][0].get("query_ref") == "order_status_check"


@pytest.mark.parametrize("case", SPEC_CASES, ids=CASE_IDS)
class TestGeneratedModels:
    """schemas/ からの生成Pydanticモデルがコアspecでも成立することのsmoke検証。"""

    def _model_class(self, case: SpecCase) -> type:
        import importlib

        from gen_models import module_name_for

        module_name = module_name_for(case.schema_filename).removesuffix(".py")
        module = importlib.import_module(f"models.{module_name}")
        return getattr(module, case.title)

    def test_generated_model_accepts_schema_example(self, case: SpecCase) -> None:
        example = load_schema(case.schema_filename)["examples"][0]
        model = self._model_class(case)(**example)
        assert model.artifact_type == case.artifact_type or (
            getattr(model.artifact_type, "value", None) == case.artifact_type
        )

    def test_generated_model_rejects_missing_domain_field(self, case: SpecCase) -> None:
        from pydantic import ValidationError as PydanticValidationError

        example = load_schema(case.schema_filename)["examples"][0]
        first_required = sorted(case.domain_required)[0]
        broken = {k: v for k, v in example.items() if k != first_required}
        with pytest.raises(PydanticValidationError):
            self._model_class(case)(**broken)
