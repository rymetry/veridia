"""Gate評価器のテスト(T-054縮小版: GateDecision + source_grounding gateのblock配線)。

意図的に厚く書いている領域:

- **blockが実際に発火すること。** 「防御コードは正常系テストでは一生発火しない」
  (learning-log 2026-07-03)。RunRecord schemaは `source_refs` に minItems: 1 を課すため、
  正常経路のrecordではsource_grounding gateは永遠にpassする。gateとして意味を持つのは
  contractを満たさないpayload(手書きrecord、将来の別producer、破損file)を渡された
  ときであり、そこを狙って落とす。
- **inconclusiveがpassへ退化しないこと。** 評価器の無いgateを黙ってpassにすると、
  16 gate中15個が未実装の現状で `decision: pass` が出てしまう。
- **stage差し替えでwarn / block経路が両方動くこと**(T-054 DoD)。
"""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from artifact_validator import validate_artifact
from gate_evaluator import (
    DECISION_BLOCK,
    DECISION_PASS,
    DECISION_WARN,
    OUTCOME_FAIL,
    OUTCOME_INCONCLUSIVE,
    OUTCOME_PASS,
    SOURCE_GROUNDING_GATE,
    GateBlockedError,
    GateDecisionNotFoundError,
    GateDecisionStore,
    GateDecisionStoreError,
    GateEvaluationError,
    GateEvaluator,
    GatePolicy,
    GatePolicyError,
    enforce,
)
from run_store import RunStore, build_run_record

REPO_ROOT = Path(__file__).parent.parent
RUN_RECORD_SCHEMA = REPO_ROOT / "schemas" / "run-record.schema.json"
REAL_POLICY_PATH = REPO_ROOT / "policies" / "gate-policy.yaml"

EVALUATED_AT = datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
IMPLEMENTED_GATES = frozenset({SOURCE_GROUNDING_GATE})


def make_run_record() -> dict[str, Any]:
    """A contract-valid RunRecord (the run-record schema's own example)."""
    schema = json.loads(RUN_RECORD_SCHEMA.read_text(encoding="utf-8"))
    return copy.deepcopy(schema["examples"][0])


def real_policy_document() -> dict[str, Any]:
    return yaml.safe_load(REAL_POLICY_PATH.read_text(encoding="utf-8"))


def write_policy(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "gate-policy.yaml"
    path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    return path


def policy_with_stages(tmp_path: Path, **stages: str) -> GatePolicy:
    """Load the real policy with the named gates moved to different stages.

    Every unnamed gate is pushed to `shadow` so a test can isolate the gate it cares
    about: shadow results are recorded but never reach the decision.
    """
    document = real_policy_document()
    for gate_id, gate in document["gates"].items():
        gate["stage"] = stages.get(gate_id, "shadow")
    return GatePolicy.load(write_policy(tmp_path, document))


@pytest.fixture
def real_policy() -> GatePolicy:
    return GatePolicy.load(REAL_POLICY_PATH)


class TestGatePolicy:
    def test_loads_the_repository_policy_by_default(self) -> None:
        policy = GatePolicy.load()

        assert policy.policy_version == real_policy_document()["policy_version"]
        assert policy.stages[SOURCE_GROUNDING_GATE] == "block"

    def test_exposes_every_gate_defined_in_the_policy(self, real_policy: GatePolicy) -> None:
        assert set(real_policy.stages) == set(real_policy_document()["gates"])

    def test_stages_cannot_be_mutated_through_the_policy(self, real_policy: GatePolicy) -> None:
        with pytest.raises(TypeError):
            real_policy.stages[SOURCE_GROUNDING_GATE] = "shadow"  # type: ignore[index]

    def test_policy_violating_its_own_schema_is_rejected(self, tmp_path: Path) -> None:
        document = real_policy_document()
        document["gates"][SOURCE_GROUNDING_GATE]["stage"] = "enforce"

        with pytest.raises(GatePolicyError, match="gate-policy"):
            GatePolicy.load(write_policy(tmp_path, document))

    def test_missing_policy_file_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(GatePolicyError, match="failed to read"):
            GatePolicy.load(tmp_path / "absent.yaml")

    def test_policy_that_is_not_a_mapping_is_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "gate-policy.yaml"
        path.write_text("- not-a-mapping\n", encoding="utf-8")

        with pytest.raises(GatePolicyError, match="mapping"):
            GatePolicy.load(path)


class TestEvaluationCoversEveryGate:
    def test_every_policy_gate_appears_in_the_results(self, real_policy: GatePolicy) -> None:
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        evaluated = {result["gate"] for result in decision["gate_results"]}
        assert evaluated == set(real_policy.stages)

    def test_gates_without_an_evaluator_are_inconclusive_not_pass(
        self, real_policy: GatePolicy
    ) -> None:
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        unimplemented = [
            result for result in decision["gate_results"] if result["gate"] not in IMPLEMENTED_GATES
        ]
        assert unimplemented
        assert {result["outcome"] for result in unimplemented} == {OUTCOME_INCONCLUSIVE}

    def test_every_result_carries_a_reason(self, real_policy: GatePolicy) -> None:
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        assert all(result["reason"].strip() for result in decision["gate_results"])

    def test_result_records_the_stage_used_at_evaluation_time(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path, source_grounding="warn")

        decision = GateEvaluator(policy=policy).evaluate(make_run_record(), created_at=EVALUATED_AT)

        assert _result_for(decision, SOURCE_GROUNDING_GATE)["stage"] == "warn"

    def test_decision_records_the_policy_version_used(self, real_policy: GatePolicy) -> None:
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        assert decision["policy_version"] == real_policy.policy_version

    def test_output_satisfies_the_gate_decision_contract(self, real_policy: GatePolicy) -> None:
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        validate_artifact(decision)


class TestSourceGroundingGate:
    def test_grounded_run_passes_the_gate(self, real_policy: GatePolicy) -> None:
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        assert _result_for(decision, SOURCE_GROUNDING_GATE)["outcome"] == OUTCOME_PASS

    @pytest.mark.parametrize(
        ("description", "source_refs"),
        [
            ("empty list", []),
            ("blank strings only", ["", "   "]),
            ("not a list", "internal://github/rymetry/veridia/pull/5"),
            ("non-string entries", [{"url": "internal://x"}]),
        ],
    )
    def test_ungrounded_run_fails_the_gate_and_blocks(
        self,
        real_policy: GatePolicy,
        description: str,
        source_refs: Any,
    ) -> None:
        record = make_run_record()
        record["source_refs"] = source_refs

        decision = GateEvaluator(policy=real_policy).evaluate(record, created_at=EVALUATED_AT)

        assert _result_for(decision, SOURCE_GROUNDING_GATE)["outcome"] == OUTCOME_FAIL, description
        assert decision["decision"] == DECISION_BLOCK
        assert any(SOURCE_GROUNDING_GATE in reason for reason in decision["blocking_reasons"])

    def test_missing_source_refs_key_fails_the_gate(self, real_policy: GatePolicy) -> None:
        record = make_run_record()
        del record["source_refs"]

        decision = GateEvaluator(policy=real_policy).evaluate(record, created_at=EVALUATED_AT)

        assert _result_for(decision, SOURCE_GROUNDING_GATE)["outcome"] == OUTCOME_FAIL

    def test_blocking_decision_still_validates_as_a_gate_decision(
        self, real_policy: GatePolicy
    ) -> None:
        record = make_run_record()
        record["source_refs"] = []

        validate_artifact(
            GateEvaluator(policy=real_policy).evaluate(record, created_at=EVALUATED_AT)
        )


class TestStageDrivesTheDecision:
    """§17.0の3段階が判定へ与える影響。stageはfixtureで差し替える(T-054 DoD)。"""

    def test_block_stage_failure_blocks(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path, source_grounding="block")
        record = make_run_record()
        record["source_refs"] = []

        decision = GateEvaluator(policy=policy).evaluate(record, created_at=EVALUATED_AT)

        assert decision["decision"] == DECISION_BLOCK
        assert decision["blocking_reasons"]
        assert decision["warning_reasons"] == []

    def test_warn_stage_failure_warns_instead_of_blocking(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path, source_grounding="warn")
        record = make_run_record()
        record["source_refs"] = []

        decision = GateEvaluator(policy=policy).evaluate(record, created_at=EVALUATED_AT)

        assert decision["decision"] == DECISION_WARN
        assert decision["blocking_reasons"] == []
        assert any(SOURCE_GROUNDING_GATE in reason for reason in decision["warning_reasons"])

    def test_shadow_stage_failure_is_recorded_but_changes_nothing(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path)  # every gate shadow
        record = make_run_record()
        record["source_refs"] = []

        decision = GateEvaluator(policy=policy).evaluate(record, created_at=EVALUATED_AT)

        assert _result_for(decision, SOURCE_GROUNDING_GATE)["outcome"] == OUTCOME_FAIL
        assert decision["decision"] == DECISION_PASS
        assert decision["blocking_reasons"] == []
        assert decision["warning_reasons"] == []

    def test_shadow_stage_inconclusive_does_not_warn(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path, source_grounding="block")

        decision = GateEvaluator(policy=policy).evaluate(make_run_record(), created_at=EVALUATED_AT)

        assert decision["decision"] == DECISION_PASS

    @pytest.mark.parametrize("stage", ["block", "warn"])
    def test_inconclusive_at_an_enforcing_stage_warns(self, tmp_path: Path, stage: str) -> None:
        # 評価器の無いgateをpass扱いにしないことの実証。oracleは未実装
        policy = policy_with_stages(tmp_path, oracle=stage)

        decision = GateEvaluator(policy=policy).evaluate(make_run_record(), created_at=EVALUATED_AT)

        assert decision["decision"] == DECISION_WARN
        assert any("oracle" in reason for reason in decision["warning_reasons"])
        assert decision["blocking_reasons"] == []

    def test_todays_real_policy_cannot_yield_pass(self, real_policy: GatePolicy) -> None:
        # 15/16 gateが未実装である事実を可視化する。実装が進めばこのテストが落ちて知らせる
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        assert decision["decision"] == DECISION_WARN


class TestSubjectDeclaredStatus:
    """自己申告gate_statusは通過の根拠にしないが、厳しい側へは効かせる。"""

    def test_declared_blocked_blocks_even_when_no_gate_fails(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path)  # every gate shadow -> nothing can block
        record = make_run_record()
        record["envelope"]["gate_status"] = "blocked"

        decision = GateEvaluator(policy=policy).evaluate(record, created_at=EVALUATED_AT)

        assert decision["subject_declared_status"] == "blocked"
        assert decision["decision"] == DECISION_BLOCK
        assert any("blocked" in reason for reason in decision["blocking_reasons"])

    def test_declared_passed_with_risks_warns(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path)
        record = make_run_record()
        record["envelope"]["gate_status"] = "passed-with-risks"

        decision = GateEvaluator(policy=policy).evaluate(record, created_at=EVALUATED_AT)

        assert decision["decision"] == DECISION_WARN
        assert decision["warning_reasons"]

    def test_declared_passed_does_not_rescue_a_failing_gate(self, tmp_path: Path) -> None:
        # 自己申告でgateを迂回できないこと(learning-log「信頼ラベルの自己申告」)
        policy = policy_with_stages(tmp_path, source_grounding="block")
        record = make_run_record()
        record["envelope"]["gate_status"] = "passed"
        record["source_refs"] = []

        decision = GateEvaluator(policy=policy).evaluate(record, created_at=EVALUATED_AT)

        assert decision["decision"] == DECISION_BLOCK

    @pytest.mark.parametrize(
        "envelope",
        [{}, {"gate_status": "not-a-status"}, "not-an-object"],
    )
    def test_unreadable_declaration_is_recorded_as_null(
        self, tmp_path: Path, envelope: Any
    ) -> None:
        policy = policy_with_stages(tmp_path)
        record = make_run_record()
        record["envelope"] = envelope

        decision = GateEvaluator(policy=policy).evaluate(record, created_at=EVALUATED_AT)

        assert decision["subject_declared_status"] is None

    def test_missing_envelope_key_is_recorded_as_null(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path)
        record = make_run_record()
        del record["envelope"]

        decision = GateEvaluator(policy=policy).evaluate(record, created_at=EVALUATED_AT)

        assert decision["subject_declared_status"] is None


class TestSubjectMustBeIdentifiable:
    """何を評価したか言えない判定recordは監査に使えないので、評価自体を拒否する。"""

    @pytest.mark.parametrize("run_id", ["", "   ", None, 42])
    def test_unusable_run_id_is_rejected(self, real_policy: GatePolicy, run_id: Any) -> None:
        record = make_run_record()
        record["run_id"] = run_id

        with pytest.raises(GateEvaluationError, match="run_id"):
            GateEvaluator(policy=real_policy).evaluate(record, created_at=EVALUATED_AT)

    def test_missing_run_id_is_rejected(self, real_policy: GatePolicy) -> None:
        record = make_run_record()
        del record["run_id"]

        with pytest.raises(GateEvaluationError, match="run_id"):
            GateEvaluator(policy=real_policy).evaluate(record, created_at=EVALUATED_AT)

    def test_gate_id_and_evidence_refs_point_at_the_evaluated_run(
        self, real_policy: GatePolicy
    ) -> None:
        record = make_run_record()

        decision = GateEvaluator(policy=real_policy).evaluate(record, created_at=EVALUATED_AT)

        assert decision["evidence_refs"] == [record["run_id"]]
        assert record["run_id"] in decision["gate_id"]

    def test_naive_created_at_is_rejected(self, real_policy: GatePolicy) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            GateEvaluator(policy=real_policy).evaluate(
                make_run_record(), created_at=datetime(2026, 8, 2, 9, 0)
            )


class TestComposesWithTheRunStore:
    """部品が単体で動くことと、実際に繋がることは別。保存済みrunに対して縦に通す。

    build_run_record → RunStore.save → RunStore.get
      → GateEvaluator.evaluate → GateDecisionStore.save → enforce
    """

    def test_stored_run_is_evaluated_and_the_decision_is_persisted(
        self, tmp_path: Path, real_policy: GatePolicy
    ) -> None:
        source = make_run_record()
        record = build_run_record(
            source["envelope"],
            run_id=source["run_id"],
            trace_id=source["trace_id"],
            agent=source["created_by"]["agent"],
            model=source["created_by"]["model"],
            source_refs=source["source_refs"],
            sqk_core_commit=source["sqk_core"]["commit"],
            created_at=EVALUATED_AT,
        )
        run_store = RunStore.open(tmp_path / "runs")
        run_store.save(record)
        gate_store = GateDecisionStore.open(tmp_path / "gates")

        decision = GateEvaluator(policy=real_policy).evaluate(
            run_store.get(source["run_id"]), created_at=EVALUATED_AT
        )
        gate_store.save(decision)

        assert _result_for(decision, SOURCE_GROUNDING_GATE)["outcome"] == OUTCOME_PASS
        assert gate_store.get(decision["gate_id"])["evidence_refs"] == [source["run_id"]]
        enforce(decision)

    def test_a_run_whose_skill_declared_blocked_stops_the_caller(
        self, tmp_path: Path, real_policy: GatePolicy
    ) -> None:
        # 「gate_status: blocked のrunが実際に止まる」の縦通し実証
        source = make_run_record()
        envelope = {**source["envelope"], "gate_status": "blocked"}
        record = build_run_record(
            envelope,
            run_id=source["run_id"],
            trace_id=source["trace_id"],
            agent=source["created_by"]["agent"],
            model=source["created_by"]["model"],
            source_refs=source["source_refs"],
            sqk_core_commit=source["sqk_core"]["commit"],
            created_at=EVALUATED_AT,
        )
        run_store = RunStore.open(tmp_path / "runs")
        run_store.save(record)

        decision = GateEvaluator(policy=real_policy).evaluate(
            run_store.get(source["run_id"]), created_at=EVALUATED_AT
        )

        # 記録は残り、そのうえで停止する(記録と停止は別ステップ)
        GateDecisionStore.open(tmp_path / "gates").save(decision)
        assert decision["decision"] == DECISION_BLOCK
        with pytest.raises(GateBlockedError):
            enforce(decision)


class TestEnforce:
    """「blockedなrunが実際に止まる」の実体。呼び出し側はこれで停止する。"""

    def test_block_raises(self, real_policy: GatePolicy) -> None:
        record = make_run_record()
        record["source_refs"] = []
        decision = GateEvaluator(policy=real_policy).evaluate(record, created_at=EVALUATED_AT)

        with pytest.raises(GateBlockedError) as excinfo:
            enforce(decision)

        assert SOURCE_GROUNDING_GATE in str(excinfo.value)

    def test_warn_does_not_raise(self, real_policy: GatePolicy) -> None:
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        assert decision["decision"] == DECISION_WARN
        enforce(decision)

    def test_pass_does_not_raise(self, tmp_path: Path) -> None:
        policy = policy_with_stages(tmp_path)
        decision = GateEvaluator(policy=policy).evaluate(make_run_record(), created_at=EVALUATED_AT)

        assert decision["decision"] == DECISION_PASS
        enforce(decision)


class TestGateDecisionStore:
    def test_save_and_get_roundtrip(self, tmp_path: Path, real_policy: GatePolicy) -> None:
        store = GateDecisionStore.open(tmp_path / "gates")
        decision = GateEvaluator(policy=real_policy).evaluate(
            make_run_record(), created_at=EVALUATED_AT
        )

        path = store.save(decision)

        assert path.is_file()
        assert store.get(decision["gate_id"]) == decision
        assert store.gate_ids() == (decision["gate_id"],)

    def test_save_rejects_a_payload_that_breaks_the_contract(self, tmp_path: Path) -> None:
        store = GateDecisionStore.open(tmp_path / "gates")

        with pytest.raises(Exception, match="artifact_type"):
            store.save({"gate_id": "GATE-1"})

    def test_get_unknown_gate_id_raises(self, tmp_path: Path) -> None:
        store = GateDecisionStore.open(tmp_path / "gates")

        with pytest.raises(GateDecisionNotFoundError):
            store.get("GATE-absent")

    @pytest.mark.parametrize("gate_id", ["../escape", "nested/child", ""])
    def test_gate_id_cannot_escape_the_store_root(self, tmp_path: Path, gate_id: str) -> None:
        store = GateDecisionStore.open(tmp_path / "gates")

        with pytest.raises(GateDecisionStoreError):
            store.get(gate_id)

    def test_unparsable_file_raises_instead_of_returning_garbage(self, tmp_path: Path) -> None:
        root = tmp_path / "gates"
        store = GateDecisionStore.open(root)
        (root / "GATE-broken.json").write_text("{not json", encoding="utf-8")

        with pytest.raises(GateDecisionStoreError, match="parse"):
            store.get("GATE-broken")

    def test_non_object_file_raises(self, tmp_path: Path) -> None:
        root = tmp_path / "gates"
        store = GateDecisionStore.open(root)
        (root / "GATE-list.json").write_text("[]", encoding="utf-8")

        with pytest.raises(GateDecisionStoreError, match="object"):
            store.get("GATE-list")


def _result_for(decision: dict[str, Any], gate: str) -> dict[str, Any]:
    matches = [result for result in decision["gate_results"] if result["gate"] == gate]
    assert len(matches) == 1, f"expected exactly one result for {gate}, got {len(matches)}"
    return matches[0]
