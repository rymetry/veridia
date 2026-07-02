"""ArtifactBase JSON Schema(schemas/artifact-base.schema.json)の契約テスト。

T-003 DoD:
- schema自体がJSON Schema meta-schema(draft 2020-12)に対してvalid
- North Star §6.1の共通必須fieldすべてが required に列挙されている
- 有効なサンプルinstanceがpassし、必須field欠落サンプルがfailする

加えてADR-0002の決定「source_refsの空配列rejectは required + minItems: 1 で担保」を検証する。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "artifact-base.schema.json"

# North Star §6.1が列挙する共通必須field。
# T-001の学び(空の required 配列は何も検証しない)への守り: schema側の required と
# この期待値の完全一致を検証し、静かな縮退を防ぐ。
SECTION_6_1_REQUIRED_FIELDS = frozenset(
    {
        "artifact_id",
        "artifact_type",
        "version",
        "source_refs",
        "created_by",
        "confidence",
        "status",
        "requires_human_review",
        "trace_id",
        "created_at",
    }
)


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def make_valid_artifact() -> dict[str, Any]:
    """§6.1の全共通fieldを満たす有効instanceを毎回新しく作る(共有状態を持たない)。"""
    return {
        "artifact_id": "REQ-001",
        "artifact_type": "requirement_spec",
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


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema())


class TestSchemaItself:
    def test_schema_file_exists(self) -> None:
        assert SCHEMA_PATH.is_file(), f"schema正本が存在しない: {SCHEMA_PATH}"

    def test_schema_is_valid_against_draft_2020_12_metaschema(self) -> None:
        # check_schema はmeta-schema違反時に SchemaError を送出する
        Draft202012Validator.check_schema(load_schema())

    def test_schema_declares_draft_2020_12(self) -> None:
        schema = load_schema()
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_required_matches_section_6_1_field_list(self) -> None:
        schema = load_schema()
        assert set(schema["required"]) == SECTION_6_1_REQUIRED_FIELDS

    def test_all_required_fields_have_property_definitions(self) -> None:
        schema = load_schema()
        missing = SECTION_6_1_REQUIRED_FIELDS - set(schema["properties"])
        assert not missing, f"required だが properties 未定義のfield: {missing}"


class TestValidInstances:
    def test_valid_sample_passes(self, validator: Draft202012Validator) -> None:
        validator.validate(make_valid_artifact())

    def test_schema_embedded_examples_pass(self, validator: Draft202012Validator) -> None:
        examples = load_schema().get("examples", [])
        assert examples, "examplesがキー欠落または空 — 空反復での素通り(vacuous pass)を防ぐ"
        for example in examples:
            validator.validate(example)

    def test_naive_created_at_passes_raw_json_validation(
        self, validator: Draft202012Validator
    ) -> None:
        # draft 2020-12のformatは既定で注釈のみのため、timezone無しのnaive datetimeも
        # 生JSON検証では通る。契約意図はRFC 3339(timezone必須)で、生成Pydanticモデル側は
        # AwareDatetimeで拒否する(test_gen_models.py参照)。生JSON側でformatを強制するかは
        # validator実装(T-008)で決める — この挙動が変わったらこのテストが検知する
        validator.validate({**make_valid_artifact(), "created_at": "2026-07-02T10:00:00"})

    def test_domain_specific_extra_fields_are_allowed(
        self, validator: Draft202012Validator
    ) -> None:
        # 各artifact schemaは allOf でArtifactBaseを継承しdomain固有fieldを足すため、
        # base側は追加プロパティを禁止しない(§6.1 / schemas/README.md)
        artifact = {**make_valid_artifact(), "requirement_text": "注文APIは冪等である"}
        validator.validate(artifact)

    @pytest.mark.parametrize("status", ["draft", "reviewed", "approved", "deprecated"])
    def test_all_section_6_1_status_values_pass(
        self, validator: Draft202012Validator, status: str
    ) -> None:
        validator.validate({**make_valid_artifact(), "status": status})

    @pytest.mark.parametrize("confidence", [0, 0.0, 0.5, 1, 1.0])
    def test_confidence_boundaries_pass(
        self, validator: Draft202012Validator, confidence: float
    ) -> None:
        validator.validate({**make_valid_artifact(), "confidence": confidence})

    @pytest.mark.parametrize("version", ["0.1.0", "1.0.0", "1.2.3-rc.1", "1.2.3+build.5"])
    def test_semver_versions_pass(self, validator: Draft202012Validator, version: str) -> None:
        validator.validate({**make_valid_artifact(), "version": version})


class TestRequiredFieldMissing:
    @pytest.mark.parametrize("field", sorted(SECTION_6_1_REQUIRED_FIELDS))
    def test_missing_required_field_fails(
        self, validator: Draft202012Validator, field: str
    ) -> None:
        artifact = {k: v for k, v in make_valid_artifact().items() if k != field}
        with pytest.raises(ValidationError):
            validator.validate(artifact)

    @pytest.mark.parametrize("subfield", ["agent", "skill", "model"])
    def test_created_by_missing_subfield_fails(
        self, validator: Draft202012Validator, subfield: str
    ) -> None:
        base = make_valid_artifact()
        created_by = {k: v for k, v in base["created_by"].items() if k != subfield}
        with pytest.raises(ValidationError):
            validator.validate({**base, "created_by": created_by})


class TestInvalidValues:
    def test_empty_source_refs_fails(self, validator: Draft202012Validator) -> None:
        # ADR-0002: required(キー存在)だけでは空配列が通るため minItems: 1 で reject する
        with pytest.raises(ValidationError):
            validator.validate({**make_valid_artifact(), "source_refs": []})

    def test_unknown_status_fails(self, validator: Draft202012Validator) -> None:
        with pytest.raises(ValidationError):
            validator.validate({**make_valid_artifact(), "status": "published"})

    @pytest.mark.parametrize("confidence", [-0.1, 1.1, "0.8"])
    def test_out_of_range_or_non_numeric_confidence_fails(
        self, validator: Draft202012Validator, confidence: Any
    ) -> None:
        with pytest.raises(ValidationError):
            validator.validate({**make_valid_artifact(), "confidence": confidence})

    @pytest.mark.parametrize("version", ["1.0", "v1.0.0", "01.0.0", ""])
    def test_non_semver_version_fails(self, validator: Draft202012Validator, version: str) -> None:
        with pytest.raises(ValidationError):
            validator.validate({**make_valid_artifact(), "version": version})

    def test_non_string_source_ref_item_fails(self, validator: Draft202012Validator) -> None:
        with pytest.raises(ValidationError):
            validator.validate({**make_valid_artifact(), "source_refs": [123]})

    def test_non_boolean_requires_human_review_fails(self, validator: Draft202012Validator) -> None:
        with pytest.raises(ValidationError):
            validator.validate({**make_valid_artifact(), "requires_human_review": "yes"})
