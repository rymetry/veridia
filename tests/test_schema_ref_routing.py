"""schema_ref の2 family routing テスト(ADR-0010 Decision 2)。

固定したい性質は1つに尽きる: **familyは名前空間だけで決まり、フォールバックしない。**
「sqk-coreで引けなければveridiaを試す」を入れると、同名schemaが両familyに現れた瞬間に
どちらを検証したのか分からないまま通る。今は衝突が無いが、無いことに依存させない。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from artifact_validator import (
    FAMILY_SQK_CORE,
    FAMILY_VERIDIA,
    VERIDIA_REF_PREFIX,
    SqkSchemaError,
    declares_sqk_core_contract,
    family_of,
    validate_envelope_artifact,
    validate_handoff_envelope,
    veridia_ref_for,
)
from artifact_validator.schema_ref import (
    available_schema_refs,
    load_schema,
    validator_for_schema_ref,
    veridia_schema_refs,
)
from artifact_validator.sqk_schema_store import available_schema_refs as sqk_schema_refs

REPO_ROOT = Path(__file__).parent.parent
SOURCE_MAP_REF = f"{VERIDIA_REF_PREFIX}source-map.schema.json"
SQK_MATRIX_REF = "schemas/condition-assignment-matrix.schema.json"


def source_map_example() -> dict[str, Any]:
    schema = json.loads(
        (REPO_ROOT / "schemas" / "source-map.schema.json").read_text(encoding="utf-8")
    )
    return json.loads(json.dumps(schema["examples"][0]))


def veridia_envelope(content: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_skill": "source-grounding",
        "phase": "W1",
        "artifacts": [{"type": "SourceMap", "schema_ref": SOURCE_MAP_REF, "content": content}],
        "trace_ids": ["SRC-001"],
        "assumptions": [],
        "open_questions": [],
        "gate_status": "passed",
    }


class TestFamilyIsDecidedByNamespaceAlone:
    def test_veridia_scheme_routes_to_veridia(self) -> None:
        assert family_of(SOURCE_MAP_REF) == FAMILY_VERIDIA

    def test_bare_relative_path_routes_to_sqk_core(self) -> None:
        assert family_of(SQK_MATRIX_REF) == FAMILY_SQK_CORE

    def test_a_veridia_filename_without_the_scheme_is_not_veridia(self) -> None:
        # フォールバックしない証拠。veridiaのschema名でも素のパスならsqk-core扱いになり、
        # sqk-coreに存在しないので解決に失敗する(黙って通らない)
        assert family_of("schemas/source-map.schema.json") == FAMILY_SQK_CORE

        with pytest.raises(SqkSchemaError):
            validator_for_schema_ref("schemas/source-map.schema.json")

    def test_ref_builder_round_trips(self) -> None:
        assert veridia_ref_for("schemas/source-map.schema.json") == SOURCE_MAP_REF


class TestVeridiaRefResolution:
    def test_resolves_a_veridia_schema(self) -> None:
        schema = load_schema(SOURCE_MAP_REF)

        assert schema["title"] == "SourceMap"

    def test_validator_resolves_inherited_refs(self) -> None:
        # veridia schemaは artifact-base.schema.json を allOf で参照する。registry無しの
        # validatorは Unresolvable で落ちる(schemas/README.md)
        validator = validator_for_schema_ref(SOURCE_MAP_REF)

        assert list(validator.iter_errors(source_map_example())) == []

    def test_inherited_constraints_are_actually_enforced(self) -> None:
        # ArtifactBase側の制約が効いていること(registryが繋がっている実証)
        payload = source_map_example()
        del payload["confidence"]

        assert list(validator_for_schema_ref(SOURCE_MAP_REF).iter_errors(payload))

    @pytest.mark.parametrize(
        "schema_ref",
        [
            f"{VERIDIA_REF_PREFIX}nope.schema.json",
            f"{VERIDIA_REF_PREFIX}../pyproject.toml",
            "veridia://nope.schema.json",
        ],
    )
    def test_unroutable_veridia_ref_raises(self, schema_ref: str) -> None:
        with pytest.raises(SqkSchemaError):
            validator_for_schema_ref(schema_ref)

    def test_listing_covers_both_families(self) -> None:
        refs = available_schema_refs()

        assert SOURCE_MAP_REF in refs
        assert set(veridia_schema_refs()) <= set(refs)
        if sqk_schema_refs():
            assert set(sqk_schema_refs()) <= set(refs)


class TestEnvelopeCarriesBothFamilies:
    def test_veridia_artifact_inside_an_envelope_validates(self) -> None:
        validate_handoff_envelope(veridia_envelope(source_map_example()))

    def test_a_broken_veridia_artifact_is_rejected_by_the_envelope_check(self) -> None:
        broken = source_map_example()
        broken["trust_level"] = "probably-fine"

        with pytest.raises(Exception, match="trust_level"):
            validate_handoff_envelope(veridia_envelope(broken))

    def test_direct_artifact_validation_routes_by_family(self) -> None:
        validate_envelope_artifact(source_map_example(), schema_ref=SOURCE_MAP_REF)


class TestDeclaresSqkCoreContract:
    def test_true_for_a_sqk_core_ref(self) -> None:
        assert declares_sqk_core_contract([{"schema_ref": SQK_MATRIX_REF}])

    def test_false_for_veridia_only(self) -> None:
        assert not declares_sqk_core_contract([{"schema_ref": SOURCE_MAP_REF}])

    def test_true_when_mixed(self) -> None:
        assert declares_sqk_core_contract(
            [{"schema_ref": SOURCE_MAP_REF}, {"schema_ref": SQK_MATRIX_REF}]
        )

    @pytest.mark.parametrize("artifacts", [None, [], "nope", [{}], [{"schema_ref": 7}], [7]])
    def test_malformed_input_answers_false_without_raising(self, artifacts: Any) -> None:
        # envelopeの形の問題はenvelope自身の契約検証が報告する。ここで二重に落とさない
        assert declares_sqk_core_contract(artifacts) is False
