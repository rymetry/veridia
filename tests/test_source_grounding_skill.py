"""T-029: veridia自前skill `source-grounding` とその実行経路(W1)。

実LLMは呼ばない(ADR-0005 Decision 3: fakeは環境変数から選べない)。

意図的に厚く書いている領域:

- **自己申告 `trust_level` が効かないこと。** ラベルの生成主体とそれを信頼する主体が
  同じなら、gateは自己申告で迂回できる(learning-log 2026-08-02 / ADR-0009 Decision 2)。
  「上書きする実装がある」ではなく「モデルが書いても値が変わらない」を固定する。
- **空のgroundingが正当な結果として通ること。** 捏造で埋める方が「成功」に見えるため、
  空配列が保存できることをテストで担保しないと、埋める実装へ流れる。
- **対象プロダクト固有の知識がpackageに混ざっていないこと**(T-029 DoD)。
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from artifact_validator import ArtifactValidationError, validate_artifact
from run_store import RunStore
from skill_runner import (
    FakeLLMClient,
    QaSkillSource,
    SkillNotFoundError,
    SkillRunner,
    SkillSourceError,
)
from skill_runner.qa_skill_source import TEMPLATE_DIR_NAME
from skill_runner.skill_source import NAME_RE
from trace_store import TraceStore

REPO_ROOT = Path(__file__).parent.parent
QA_SKILLS_DIR = REPO_ROOT / "qa-skills"
PACKAGE = QA_SKILLS_DIR / "source-grounding"
SKILL = "source-grounding"
SOURCE_MAP_REF = "veridia://schemas/source-map.schema.json"
SOURCE_REFS = ["git://veridia/aaaa...bbbb"]

PACKAGE_FILES = (
    "SKILL.md",
    "manifest.yaml",
    "input.schema.json",
    "output.schema.json",
    "changelog.md",
    "preconditions.md",
    "postconditions.md",
    "failure_modes.md",
)


def source_map(**overrides: Any) -> dict[str, Any]:
    schema = json.loads((REPO_ROOT / "schemas" / "source-map.schema.json").read_text("utf-8"))
    return {**json.loads(json.dumps(schema["examples"][0])), **overrides}


def envelope(content: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    return {
        "source_skill": SKILL,
        "phase": "W1",
        "artifacts": [
            {
                "type": "SourceMap",
                "schema_ref": SOURCE_MAP_REF,
                "content": source_map() if content is None else content,
            }
        ],
        "trace_ids": ["SRC-001"],
        "assumptions": [],
        "open_questions": [],
        "gate_status": "passed",
        **overrides,
    }


def make_runner(tmp_path: Path, responses: list[dict[str, Any]]) -> tuple[SkillRunner, RunStore]:
    store = RunStore.open(tmp_path / "runs")
    runner = SkillRunner(
        llm_client=FakeLLMClient(responses=responses),
        run_store=store,
        trace_store=TraceStore.open(tmp_path / "trace"),
        skill_source=QaSkillSource(),
    )
    return runner, store


class TestPackageStructure:
    @pytest.mark.parametrize("filename", PACKAGE_FILES)
    def test_required_file_exists(self, filename: str) -> None:
        assert (PACKAGE / filename).is_file()

    def test_registered_in_the_registry(self) -> None:
        registry = yaml.safe_load((QA_SKILLS_DIR / "registry.yaml").read_text("utf-8"))
        entry = next(e for e in registry["skills"] if e["skill_id"] == SKILL)

        assert entry["package_path"] == SKILL
        assert (
            entry["version"]
            == yaml.safe_load((PACKAGE / "manifest.yaml").read_text("utf-8"))["version"]
        )
        assert entry["allowed_tools"] == [], "W1は推論のみ。tool実行を必要としない"

    def test_evals_carry_positive_and_negative_cases(self) -> None:
        positive = list(csv.DictReader((PACKAGE / "evals" / "positive_prompts.csv").open()))
        negative = list(csv.DictReader((PACKAGE / "evals" / "negative_prompts.csv").open()))

        assert positive and negative
        assert all(row["prompt"].strip() for row in positive + negative)

    def test_regression_cases_cover_the_fabrication_failure_modes(self) -> None:
        cases = yaml.safe_load((PACKAGE / "evals" / "regression_cases.yaml").read_text("utf-8"))
        expectations = {case["expected"] for case in cases["cases"]}

        assert "empty-extracted-items" in expectations, "空groundingを埋めない case が要る"
        assert "no-artifact-id" in expectations, "ID捏造を防ぐ case が要る"
        assert "trust-level-overwritten-by-ingestion" in expectations


class TestPackageCarriesNoTargetKnowledge:
    """対象プロダクト固有の知識をskill本体へ埋め込まない(計画§1 / T-029 DoD)。"""

    def test_no_target_specific_names_appear_in_the_package(self) -> None:
        # Phase 1の対象はveridia自身(T-024)。対象名がpackageに現れたら、対象を替えた
        # 瞬間にskillが嘘をつく。固有情報は入力として渡す
        forbidden = ("veridia自身", "run_store", "evidence_store", "RunRecord", "ExecutionEvidence")
        text = "\n".join(
            (PACKAGE / name).read_text("utf-8")
            for name in ("SKILL.md", "manifest.yaml", "preconditions.md", "postconditions.md")
        )

        for term in forbidden:
            assert term not in text, f"対象固有の知識がskillへ漏れている: {term}"

    def test_skill_states_that_input_is_data_not_instructions(self) -> None:
        # §16.4。diffの中身を指示として実行させない
        assert "指示ではない" in (PACKAGE / "SKILL.md").read_text("utf-8")


class TestQaSkillSource:
    def test_loads_the_package(self) -> None:
        skill = QaSkillSource().load(SKILL)

        assert skill.name == SKILL
        assert skill.version == "0.1.0"
        assert skill.instruction_text

    def test_resolves_declared_outputs_to_veridia_schema_refs(self) -> None:
        # manifestは成果物をtitle(SourceMap)で宣言する。実在する契約へ解決できること
        assert QaSkillSource().load(SKILL).output_schema_refs == (SOURCE_MAP_REF,)

    def test_template_is_not_executable(self) -> None:
        # _template はコピー元であって実行対象ではない
        assert TEMPLATE_DIR_NAME not in QaSkillSource().available()

        with pytest.raises(SkillNotFoundError):
            QaSkillSource().load(TEMPLATE_DIR_NAME)

    def test_scaffold_name_cannot_be_a_skill_name(self) -> None:
        # 上のテストが依存している前提そのものを固定する。scaffoldを `template` 等へ
        # 改名すると除外が効かなくなるため、そのときはここが落ちて理由ごと知らせる
        assert NAME_RE.match(TEMPLATE_DIR_NAME) is None

    def test_unknown_skill_raises(self) -> None:
        with pytest.raises(SkillNotFoundError, match="absent-skill"):
            QaSkillSource().load("absent-skill")

    def test_manifest_breaking_its_contract_is_rejected_at_load(self, tmp_path: Path) -> None:
        package = tmp_path / SKILL
        package.mkdir()
        (package / "SKILL.md").write_text("body", encoding="utf-8")
        (package / "manifest.yaml").write_text("name: source-grounding\n", encoding="utf-8")
        (tmp_path / "manifest.schema.json").write_text(
            (QA_SKILLS_DIR / "manifest.schema.json").read_text("utf-8"), encoding="utf-8"
        )

        with pytest.raises(SkillSourceError, match="manifest contract"):
            QaSkillSource(root=tmp_path).load(SKILL)

    def test_manifest_name_must_match_its_directory(self, tmp_path: Path) -> None:
        package = tmp_path / SKILL
        package.mkdir()
        (package / "SKILL.md").write_text("body", encoding="utf-8")
        manifest = yaml.safe_load((PACKAGE / "manifest.yaml").read_text("utf-8"))
        manifest["name"] = "something-else"
        (package / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
        (tmp_path / "manifest.schema.json").write_text(
            (QA_SKILLS_DIR / "manifest.schema.json").read_text("utf-8"), encoding="utf-8"
        )

        with pytest.raises(SkillSourceError, match="does not match its directory"):
            QaSkillSource(root=tmp_path).load(SKILL)


class TestW1EndToEnd:
    def test_produces_and_stores_a_source_map(self, tmp_path: Path) -> None:
        runner, store = make_runner(tmp_path, [envelope()])

        result = runner.run(
            SKILL,
            input_text="{}",
            source_refs=SOURCE_REFS,
            agent="pytest",
            authoritative_fields={"trust_level": "trusted"},
        )

        stored = store.get(result.run_id)
        artifact = stored["envelope"]["artifacts"][0]
        assert artifact["schema_ref"] == SOURCE_MAP_REF
        assert stored["status"] == "draft", "producerは常にdraftを出す"
        validate_artifact(artifact["content"])

    def test_the_record_carries_no_sqk_core_pin(self, tmp_path: Path) -> None:
        # veridia自前skillの実行にはsqk-core契約が無い(ADR-0010 Decision 3)
        runner, store = make_runner(tmp_path, [envelope()])

        result = runner.run(
            SKILL,
            input_text="{}",
            source_refs=SOURCE_REFS,
            agent="pytest",
            authoritative_fields={"trust_level": "trusted"},
        )

        assert "sqk_core" not in store.get(result.run_id)

    def test_declared_schema_ref_is_pinned_in_the_prompt_schema(self, tmp_path: Path) -> None:
        runner, _ = make_runner(tmp_path, [envelope()])
        client = runner.llm_client

        runner.run(
            SKILL,
            input_text="{}",
            source_refs=SOURCE_REFS,
            agent="pytest",
            authoritative_fields={"trust_level": "trusted"},
        )

        _, output_schema = client.calls[0]  # type: ignore[attr-defined]
        enum = output_schema["properties"]["artifacts"]["items"]["properties"]["schema_ref"]["enum"]
        assert enum == [SOURCE_MAP_REF], "モデルが契約を発明できないようenumで固定する"

    def test_a_broken_source_map_never_becomes_a_record(self, tmp_path: Path) -> None:
        runner, store = make_runner(tmp_path, [envelope(source_map(source_type="telepathy"))])

        with pytest.raises(ArtifactValidationError):
            runner.run(
                SKILL,
                input_text="{}",
                source_refs=SOURCE_REFS,
                agent="pytest",
                authoritative_fields={"trust_level": "trusted"},
            )

        assert store.run_ids() == ()


class TestTrustLabelCannotBeSelfCertified:
    """ADR-0009 Decision 2 の実効性。モデルが何を書いても取り込み層の値になる。"""

    @pytest.mark.parametrize("claimed", ["trusted", "external", "untrusted"])
    def test_model_supplied_trust_level_is_overwritten(self, tmp_path: Path, claimed: str) -> None:
        runner, store = make_runner(tmp_path, [envelope(source_map(trust_level=claimed))])

        result = runner.run(
            SKILL,
            input_text="{}",
            source_refs=SOURCE_REFS,
            agent="pytest",
            authoritative_fields={"trust_level": "external"},
        )

        content = store.get(result.run_id)["envelope"]["artifacts"][0]["content"]
        assert content["trust_level"] == "external"

    def test_a_model_that_omits_it_still_gets_the_ingestion_value(self, tmp_path: Path) -> None:
        without = source_map()
        del without["trust_level"]
        runner, store = make_runner(tmp_path, [envelope(without)])

        result = runner.run(
            SKILL,
            input_text="{}",
            source_refs=SOURCE_REFS,
            agent="pytest",
            authoritative_fields={"trust_level": "untrusted"},
        )

        content = store.get(result.run_id)["envelope"]["artifacts"][0]["content"]
        assert content["trust_level"] == "untrusted"

    def test_the_caller_object_is_not_mutated(self, tmp_path: Path) -> None:
        response = envelope(source_map(trust_level="trusted"))
        runner, _ = make_runner(tmp_path, [response])

        runner.run(
            SKILL,
            input_text="{}",
            source_refs=SOURCE_REFS,
            agent="pytest",
            authoritative_fields={"trust_level": "external"},
        )

        assert response["artifacts"][0]["content"]["trust_level"] == "trusted"


class TestEntryScript:
    """`scripts/run_skill.py` は実LLMを呼ぶ入口。ここでは呼ぶ手前の門番だけを見る。"""

    @staticmethod
    def _load_module() -> Any:
        import importlib.util

        path = PACKAGE / "scripts" / "run_skill.py"
        spec = importlib.util.spec_from_file_location("source_grounding_run_skill", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_missing_change_set_exits_with_an_input_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert self._load_module().main([str(tmp_path / "absent.json")]) == 2
        assert "failed to read" in capsys.readouterr().err

    def test_change_set_without_source_refs_is_refused_before_spending(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # 空のsourceでLLMを呼ぶと、コストだけ払って必ずgateに落ちる
        change = tmp_path / "change.json"
        change.write_text(json.dumps({"source_refs": []}), encoding="utf-8")

        assert self._load_module().main([str(change)]) == 2
        assert "source_refs" in capsys.readouterr().err


class TestEmptyGroundingIsAValidResult:
    def test_no_extracted_items_is_stored_rather_than_filled(self, tmp_path: Path) -> None:
        # 捏造して埋める方が「成功」に見えるため、空が通ることを担保しておく
        runner, store = make_runner(
            tmp_path,
            [
                envelope(
                    source_map(extracted_items=[]),
                    gate_status="passed-with-risks",
                    open_questions=["変更に対応するsourceを特定できなかった"],
                )
            ],
        )

        result = runner.run(
            SKILL,
            input_text="{}",
            source_refs=SOURCE_REFS,
            agent="pytest",
            authoritative_fields={"trust_level": "trusted"},
        )

        stored = store.get(result.run_id)
        assert stored["envelope"]["artifacts"][0]["content"]["extracted_items"] == []
        assert stored["envelope"]["gate_status"] == "passed-with-risks"
        assert stored["envelope"]["open_questions"]
