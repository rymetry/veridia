---
task_id: T-057
epic: reporting-gate
plan_ref: phase-1-crud-mvp.md#6-gate段階方針170適用
status: done
owner:
blocked_by:
---

# T-057: GateDecision契約 + source_grounding gateのblock配線(T-054の先行部分)

## 目的

`policies/gate-policy.yaml` は17 gateを定義しているが、Phase 0完了時点で評価するコードが1行も無い。
T-054本体は `blocked_by: [T-032, T-036, T-043, T-049, T-053]` で当面着手できないため、
そのうち**依存の無い部分だけ**を先に通し、gateが実際にblockする経路を1本作る。

縮小の判断: 現状の材料(RunRecord)で評価できるgateは `source_grounding` のみ。§17.0がblock開始と
定める残り3 gate(oracle / evidence / security)は入力を生むproducerがまだ無い。
評価できないgateをpass扱いにしないことを契約側で保証したうえで、実装は1 gateから始める。

## 参照

- 計画: §6(Gate段階方針。正本は `policies/gate-policy.yaml`)
- North Star: §6.24(GateDecision)、§17.0(段階的enforcement)、§17.1(gate種別)
- 先行: T-023(gate-policy.yaml)、T-027(RunRecord / RunStore)
- 本体: [T-054](T-054-gate-decision-enforcement.md)(残りのDoDはここが持つ)

## DoD

- [x] `schemas/gate-decision.schema.json` が§6.24準拠で作成され、`artifact_validator` の
      `artifact_type` ルーティングに乗り、契約テストがpassする(`tests/test_gate_decision_schema.py`、40件)
- [x] ArtifactBaseを継承しない判断と、その理由(決定的producerは `confidence` /
      `created_by.skill` / `created_by.model` を供給できない)がschema descriptionと
      契約テストで固定されている
- [x] `gate_evaluator` が `policies/gate-policy.yaml` を読み(schema検証つき)、
      policyに定義された全gateを評価して `GateDecision` を出せる
- [x] `source_grounding` gateがblock stageで**実際にblockする**。発火・非発火の両方をテストで実証
      (`TestSourceGroundingGate` / `TestStageDrivesTheDecision::test_block_stage_failure_blocks`)
- [x] 評価器の無いgateは `inconclusive` として記録され、`pass` にならない
      (`test_gates_without_an_evaluator_are_inconclusive_not_pass`)。
      現在のpolicyでは `decision: pass` が出ないことをテストで固定した
      (`test_todays_real_policy_cannot_yield_pass`)
- [x] stageをテストfixtureで差し替えるとwarn / block / shadowの各経路が実際に動く
      (`TestStageDrivesTheDecision`。実運用stageは `gate-policy.yaml` のまま変更していない)
- [x] blockした判定で呼び出し側が実際に停止できる(`enforce` が `GateBlockedError` を送出)
- [x] `GateDecisionStore` が判定を保存・取得でき、traversalを拒否する
- [x] 全テストがpassする(`VERIDIA_REQUIRE_SQK=1 uv run pytest`)

## 検証方法・根拠

```bash
VERIDIA_REQUIRE_SQK=1 uv run pytest -q
uv run ruff check . && uv run ruff format --check .
```

- 新規テスト: `tests/test_gate_decision_schema.py`(40件)、`tests/test_gate_evaluator.py`(51件)
- **mutation checkで防御テストの実効性を確認した**(全緑はDoDの必要条件でしかない。learning-log 2026-07-03)。
  実装へ意図的に6件の欠陥を入れ、いずれもテストが検出することを確認:
  inconclusiveをpass扱い / shadowをenforce扱い / 自己申告 `passed` でgate免除 /
  source_groundingを常にpass / 空白文字列をrefとして数える / `enforce` が何もしない /
  policyのschema検証をskip
- gate-policy.yaml は変更していない(stage変更はT-036 / T-043 / T-054の担当。CHANGELOG記帳も不要)

## 記録(完了時に記入)

- learning-log: [2026-08-02 契約が既に強制している条件をgateにすると、gateは一生発火しない](../../knowledge/learning-log.md)
- learning-log: [2026-08-02 未実装gateをblockにすると初日で全runが止まる](../../knowledge/learning-log.md)
- decisions: なし(ADR-0007で決めた「veridia固有4契約」の4本目であり、新たな逸脱判断は無い)
- schemas/README.md: ArtifactBase非継承の例外条件を「入れ物かどうか」から
  「producerが必須fieldの真実を供給できるか」へ一般化した
