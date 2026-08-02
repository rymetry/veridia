"""CLIへ渡す出力schemaのportable profile投影(ADR-0005 Decision 6.1)。

このモジュールは**実測された失敗から生まれた**。2026-08-02、PR #14 を対象に
`source-grounding` を実LLMで初めて回したところ、envelope が渡す content schema が
`{"type": "object"}` だったため、モデルは SourceMap の形を一切知らないまま出力し、
契約検証で全面的に弾かれた(所要4分49秒、記録は1件も残らず)。

弾かれた3種はいずれも portable profile の内側で表現できるものだった。以下のテストは
その3種を名指しで固定する — 同じ理由で再び落ちないように。
"""

from __future__ import annotations

from typing import Any

import pytest
from artifact_validator import SqkSchemaError
from skill_runner.envelope_schema import portable_envelope_schema
from skill_runner.portable_schema import PORTABLE_KEYWORDS, portable_projection

SOURCE_MAP_REF = "veridia://schemas/source-map.schema.json"
ARTIFACT_BASE_REQUIRED = {
    "artifact_id",
    "created_by",
    "requires_human_review",
    "source_refs",
    "status",
    "trace_id",
    "confidence",
    "created_at",
    "version",
}


@pytest.fixture(scope="module")
def projection() -> dict[str, Any]:
    return portable_projection(SOURCE_MAP_REF)


def walk_keywords(node: Any, path: str = "$") -> list[str]:
    """Every keyword outside the portable profile, with where it appeared."""
    if not isinstance(node, dict):
        return []
    outside: list[str] = []
    for key, value in node.items():
        if key == "properties":
            for name, subschema in value.items():
                outside += walk_keywords(subschema, f"{path}.{name}")
        elif key == "items":
            outside += walk_keywords(value, f"{path}[]")
        elif key not in PORTABLE_KEYWORDS:
            outside.append(f"{path}:{key}")
    return outside


class TestTheThreeObservedFailures:
    """実行1回で観測された3種。どれも profile 内で防げた。"""

    def test_inherited_required_fields_reach_the_model(self, projection: dict[str, Any]) -> None:
        # 実測: artifact_id / created_by.agent / requires_human_review / source_refs /
        # status / trace_id の6つが欠落した。ArtifactBaseは allOf + $ref の先にある
        assert set(projection["required"]) >= ARTIFACT_BASE_REQUIRED

    def test_item_objects_are_closed(self, projection: dict[str, Any]) -> None:
        # 実測: extracted_items の大半に label / note が生えた
        item = projection["properties"]["extracted_items"]["items"]

        assert item["additionalProperties"] is False
        assert set(item["properties"]) == {"span", "artifact_id", "confidence"}
        assert item["required"] == ["span"]

    def test_enums_reach_the_model(self, projection: dict[str, Any]) -> None:
        # 実測: source_type に 'diff' が入った
        assert projection["properties"]["source_type"]["enum"] == [
            "git_commit_range",
            "github_pr",
            "document",
        ]


class TestProjectionRules:
    def test_const_becomes_a_single_valued_enum(self, projection: dict[str, Any]) -> None:
        # const は profile 外。同義の enum へ翻訳しないと artifact_type が伝わらない
        assert projection["properties"]["artifact_type"]["enum"] == ["source_map"]

    def test_unevaluated_properties_false_becomes_additional_properties_false(
        self, projection: dict[str, Any]
    ) -> None:
        # 継承をinline済みなので等価。これが無いとtop-levelに余計なfieldが生える
        assert projection["additionalProperties"] is False

    def test_internal_defs_are_inlined(self, projection: dict[str, Any]) -> None:
        # #/$defs/extractedItem が解決されていること($defs自体は落ちる)
        assert "$defs" not in projection
        assert "span" in projection["properties"]["extracted_items"]["items"]["properties"]

    def test_nothing_outside_the_portable_profile_survives(
        self, projection: dict[str, Any]
    ) -> None:
        # profile外を残すとbackendがschemaを拒否しうる(ADR-0005 Decision 6.1の前提)
        assert walk_keywords(projection) == []

    def test_pattern_is_dropped_here_and_carried_by_contract_note(self) -> None:
        # patternはprofile外。落とすが、伝達経路が消えるわけではない
        from skill_runner.contract_note import contract_note

        assert "pattern" not in str(portable_projection(SOURCE_MAP_REF))
        assert "`version`" in contract_note((SOURCE_MAP_REF,))

    def test_projects_a_sqk_core_contract_too(self) -> None:
        # family非依存。sqk-core契約でも同じ投影が働く
        from artifact_validator.sqk_schema_store import available_schema_refs

        if not available_schema_refs():
            pytest.skip("vendor/sqk-core submodule not checked out")
        projected = portable_projection("schemas/test-architecture-element.schema.json")

        assert projected.get("type") == "object"
        assert walk_keywords(projected) == []


class TestEnvelopeEmbedsIt:
    def test_single_declared_output_is_embedded(self) -> None:
        schema = portable_envelope_schema((SOURCE_MAP_REF,))
        content = schema["properties"]["artifacts"]["items"]["properties"]["content"]

        assert content["properties"], "モデルへ渡すcontent schemaが空のobjectのままになっている"
        assert set(content["required"]) >= ARTIFACT_BASE_REQUIRED

    def test_several_declared_outputs_fall_back_to_an_open_object(self) -> None:
        # artifactごとに形が違うため1つのschemaで書けない。contract_noteは全refを覆う
        schema = portable_envelope_schema(
            (SOURCE_MAP_REF, "veridia://schemas/run-record.schema.json")
        )
        content = schema["properties"]["artifacts"]["items"]["properties"]["content"]

        assert content == {"type": "object"}

    def test_no_declared_output_falls_back_to_an_open_object(self) -> None:
        content = portable_envelope_schema(())["properties"]["artifacts"]["items"]["properties"][
            "content"
        ]

        assert content == {"type": "object"}

    def test_an_unresolvable_ref_does_not_break_prompt_construction(self) -> None:
        # 解決不能はskill source側が報告する問題。ここで落とすと原因が遠くなる
        content = portable_envelope_schema(("veridia://schemas/absent.schema.json",))["properties"][
            "artifacts"
        ]["items"]["properties"]["content"]

        assert content == {"type": "object"}

    def test_unresolvable_ref_still_raises_where_it_should(self) -> None:
        with pytest.raises(SqkSchemaError):
            portable_projection("veridia://schemas/absent.schema.json")
