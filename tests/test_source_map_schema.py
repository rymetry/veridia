"""SourceMap契約テスト(North Star §6.2 / W1の出力契約)。

RunRecord / GateDecision と違い **ArtifactBaseを継承する**。producerは
source-grounding skill(LLM)であり、`confidence` も `created_by.skill` / `model` も
真実を供給できるため。非継承の例外を増やさない側の実例として固定する。

`trust_level` の値をLLMが決めてよいかは契約の外側の問題(ADR-0009 Decision 2)。
schemaは値域しか縛れないので、authorityの配線はT-029のテストが担う。
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
SCHEMA_FILENAME = "source-map.schema.json"
ARTIFACT_TYPE = "source_map"

ARTIFACT_BASE_REQUIRED = {
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
DOMAIN_REQUIRED = {
    "source_id",
    "source_type",
    "uri",
    "source_version",
    "trust_level",
    "extracted_items",
}
TRUST_LEVELS = {"trusted", "untrusted", "external"}


@cache
def load_schema() -> dict[str, Any]:
    return json.loads((SCHEMAS_DIR / SCHEMA_FILENAME).read_text(encoding="utf-8"))


def make_valid_source_map() -> dict[str, Any]:
    return copy.deepcopy(load_schema()["examples"][0])


class TestSchemaItself:
    def test_schema_is_valid_against_draft_2020_12_metaschema(self) -> None:
        Draft202012Validator.check_schema(load_schema())

    def test_artifact_type_is_fixed_by_const(self) -> None:
        assert load_schema()["properties"]["artifact_type"]["const"] == ARTIFACT_TYPE

    def test_inherits_artifact_base(self) -> None:
        # 非継承の例外(RunRecord / GateDecision)を増やさない。producerはLLMなので
        # confidence / created_by.skill / model を供給できる
        refs = {entry.get("$ref") for entry in load_schema()["allOf"]}

        assert "artifact-base.schema.json" in refs

    def test_domain_required_matches_expected(self) -> None:
        assert set(load_schema()["required"]) == DOMAIN_REQUIRED

    def test_does_not_redeclare_a_version_field_for_the_source_revision(self) -> None:
        # §6.2の例は `version` にcommit shaを入れるが、ArtifactBaseの `version` は
        # artifact自身のsemverである。意味衝突を避けて `source_version` へ改名した
        assert "source_version" in load_schema()["properties"]
        assert "version" not in load_schema()["properties"]

    def test_trust_level_enum_matches_the_north_star(self) -> None:
        assert set(load_schema()["properties"]["trust_level"]["enum"]) == TRUST_LEVELS

    def test_extracted_item_requires_a_span(self) -> None:
        # 位置を言えない項目はgroundingになっていない
        item = load_schema()["$defs"]["extractedItem"]

        assert "span" in item["required"]

    def test_extracted_item_does_not_require_an_artifact_id(self) -> None:
        # W1時点では対応するartifact(REQ-nnn等)がまだ存在しない。必須にすると
        # producerにID捏造を強いる(learning-log「必須度は最初のproducerと突き合わせる」)
        item = load_schema()["$defs"]["extractedItem"]

        assert "artifact_id" in item["properties"]
        assert "artifact_id" not in item["required"]

    def test_is_closed_to_additional_properties(self) -> None:
        assert load_schema()["unevaluatedProperties"] is False


class TestValidPayload:
    def test_embedded_example_passes(self) -> None:
        validate_artifact(make_valid_source_map())

    def test_router_resolves_source_map_artifact_type(self) -> None:
        from artifact_validator.schema_store import artifact_type_to_schema

        assert artifact_type_to_schema()[ARTIFACT_TYPE] == SCHEMA_FILENAME

    @pytest.mark.parametrize("trust_level", sorted(TRUST_LEVELS))
    def test_every_trust_level_is_accepted(self, trust_level: str) -> None:
        payload = make_valid_source_map()
        payload["trust_level"] = trust_level

        validate_artifact(payload)

    def test_extracted_items_may_be_empty(self) -> None:
        # 「このsourceからは何も取れなかった」は正当な結果。捏造させない
        payload = make_valid_source_map()
        payload["extracted_items"] = []

        validate_artifact(payload)

    def test_item_without_artifact_id_or_confidence_passes(self) -> None:
        payload = make_valid_source_map()
        payload["extracted_items"] = [{"span": "source_connector/connector.py:L60-L98"}]

        validate_artifact(payload)


class TestInvalidPayload:
    @pytest.mark.parametrize("field", sorted(DOMAIN_REQUIRED | ARTIFACT_BASE_REQUIRED))
    def test_missing_required_field_fails(self, field: str) -> None:
        payload = make_valid_source_map()
        del payload[field]

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    def test_unknown_top_level_field_fails(self) -> None:
        payload = make_valid_source_map()
        payload["trust_reason"] = "looks fine"

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    def test_empty_source_refs_fails(self) -> None:
        # ArtifactBase側の強制。groundingのartifact自身が根拠を持たないのは矛盾
        payload = make_valid_source_map()
        payload["source_refs"] = []

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            ("trust_level", "probably-fine"),
            ("source_type", "telepathy"),
            ("uri", ""),
            ("source_id", ""),
            ("source_version", ""),
            ("extracted_items", {"span": "a:L1"}),
        ],
    )
    def test_invalid_field_value_fails(self, field: str, invalid_value: Any) -> None:
        payload = make_valid_source_map()
        payload[field] = invalid_value

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            ("span", ""),
            ("artifact_id", ""),
            ("confidence", 1.5),
            ("confidence", "high"),
        ],
    )
    def test_invalid_extracted_item_value_fails(self, field: str, invalid_value: Any) -> None:
        payload = make_valid_source_map()
        payload["extracted_items"][0][field] = invalid_value

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)

    def test_unknown_extracted_item_field_fails(self) -> None:
        payload = make_valid_source_map()
        payload["extracted_items"][0]["trust_level"] = "trusted"

        with pytest.raises(ArtifactValidationError):
            validate_artifact(payload)
