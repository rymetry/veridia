"""RunRecord契約テスト(ADR-0007の監査ラッパー)。

RunRecordは **ArtifactBase(§6.1)を継承しない**。artifactではなくartifactを運ぶrunの
記録であり、ArtifactBase必須の `confidence` はrunに対して意味を持たないため
(learning-log 2026-07-02「契約の必須度は最初のproducerのDoDと突き合わせる」)。
本ファイルはその設計判断も含めて固定する。
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

import pytest
from artifact_validator import ArtifactValidationError, validate_artifact
from jsonschema import Draft202012Validator

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
SCHEMA_FILENAME = "run-record.schema.json"
ARTIFACT_TYPE = "run_record"
DOMAIN_REQUIRED = {
    "artifact_type",
    "version",
    "run_id",
    "trace_id",
    "created_at",
    "created_by",
    "source_refs",
    "sqk_core",
    "status",
    "requires_human_review",
    "envelope",
}


@cache
def load_schema() -> dict[str, Any]:
    return json.loads((SCHEMAS_DIR / SCHEMA_FILENAME).read_text(encoding="utf-8"))


def make_valid_record() -> dict[str, Any]:
    """schema埋め込みexampleの複製(共有状態を持たない)。"""
    return json.loads(json.dumps(load_schema()["examples"][0]))


class TestSchemaItself:
    def test_schema_is_valid_against_draft_2020_12_metaschema(self) -> None:
        Draft202012Validator.check_schema(load_schema())

    def test_artifact_type_is_fixed_by_const(self) -> None:
        assert load_schema()["properties"]["artifact_type"]["const"] == ARTIFACT_TYPE

    def test_required_matches_expected(self) -> None:
        assert set(load_schema()["required"]) == DOMAIN_REQUIRED

    def test_does_not_inherit_artifact_base(self) -> None:
        # 意図的な非継承(ADR-0007)。継承へ変える場合は confidence の意味づけを先に決める
        assert "allOf" not in load_schema()

    def test_does_not_require_confidence(self) -> None:
        # ArtifactBaseを継承しない理由そのもの。runに較正されたconfidenceは存在しない
        assert "confidence" not in load_schema()["properties"]

    def test_declares_requires_human_review_without_inheriting_base(self) -> None:
        # T-027 DoD が要求するfield。confidenceと違いproducerが真実を供給できる
        # (Phase 1のLLM出力は候補生成+人間レビュー必須。計画§7)ため必須にできる
        assert load_schema()["properties"]["requires_human_review"]["type"] == "boolean"
        assert "requires_human_review" in load_schema()["required"]


class TestValidInstances:
    def test_schema_embedded_example_passes(self) -> None:
        validate_artifact(make_valid_record())

    def test_validator_routes_run_record_by_artifact_type(self) -> None:
        # ArtifactBase非継承でも artifact_type const だけでルーティングされる
        validate_artifact(make_valid_record())


class TestRequiredFields:
    @pytest.mark.parametrize("missing", sorted(DOMAIN_REQUIRED - {"artifact_type"}))
    def test_missing_required_field_fails(self, missing: str) -> None:
        record = {k: v for k, v in make_valid_record().items() if k != missing}
        with pytest.raises(ArtifactValidationError):
            validate_artifact(record)

    def test_empty_source_refs_fails(self) -> None:
        # source groundingはveridiaが実際に強制している唯一のgate。空を通さない
        with pytest.raises(ArtifactValidationError):
            validate_artifact({**make_valid_record(), "source_refs": []})

    def test_unknown_field_fails(self) -> None:
        with pytest.raises(ArtifactValidationError):
            validate_artifact({**make_valid_record(), "unexpected": "x"})


class TestAuditFieldValues:
    def test_naive_created_at_fails(self) -> None:
        # timezone必須はFormatChecker(T-008)が強制する
        with pytest.raises(ArtifactValidationError):
            validate_artifact({**make_valid_record(), "created_at": "2026-08-02T09:00:00"})

    @pytest.mark.parametrize("bad_commit", ["54e78cc", "", "z" * 40, "54E78CC7" + "a" * 32])
    def test_sqk_core_commit_must_be_full_lowercase_sha(self, bad_commit: str) -> None:
        # 短縮SHAを許すと、どの契約版かを後から一意に解決できない
        record = make_valid_record()
        record["sqk_core"] = {"commit": bad_commit}
        with pytest.raises(ArtifactValidationError):
            validate_artifact(record)

    def test_sqk_core_is_required_because_contracts_move_with_the_sha(self) -> None:
        record = {k: v for k, v in make_valid_record().items() if k != "sqk_core"}
        with pytest.raises(ArtifactValidationError):
            validate_artifact(record)

    @pytest.mark.parametrize("status", ["draft", "reviewed", "approved"])
    def test_review_statuses_pass(self, status: str) -> None:
        validate_artifact({**make_valid_record(), "status": status})

    def test_deprecated_is_not_a_run_status(self) -> None:
        # ArtifactBaseのenumから deprecated を除いた集合(runは非推奨化しない)
        with pytest.raises(ArtifactValidationError):
            validate_artifact({**make_valid_record(), "status": "deprecated"})

    def test_created_by_does_not_carry_skill_name(self) -> None:
        # skill名の正本は envelope.source_skill。二重管理を作らない
        assert "skill" not in load_schema()["properties"]["created_by"]["properties"]
        record = make_valid_record()
        record["created_by"] = {**record["created_by"], "skill": "test-architecture-design"}
        with pytest.raises(ArtifactValidationError):
            validate_artifact(record)
