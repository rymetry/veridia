---
task_id: T-054
epic: reporting-gate
plan_ref: phase-1-crud-mvp.md#6-gate段階方針170適用
status: not_started
owner:
blocked_by: [T-032, T-036, T-043, T-049, T-053]
---

# T-054: GateDecision schema + gate段階運用の配線(W18)

## 目的

gate評価結果をGateDecision(§6.24)として記録するschemaを定義し、計画§6のgate段階方針(block 4 gate / shadow群 / precision計測)を一気通貫で配線する(W18)。Phase 1完了条件「duplicate test candidateをblock/warnできる」の警告経路と、release判断の監査可能性をここで完成させる。

## 参照

- 計画: §6(Gate段階方針: block4 = source grounding / oracle / evidence / security、shadow群、正本は `policies/gate-policy.yaml`)
- North Star: §6.24(GateDecision)、§17.0〜17.4、§19.7(gate運用KPI)
- Phase 0: T-023(gate-policy.yaml。§17.1全gate定義済み・初期block 4 gate限定)

## DoD

> **先行実装あり([T-057](T-057-gate-decision-source-grounding.md), done)。** 依存の無い部分
> (GateDecision契約 / gate評価器 / source_grounding gateのblock配線 / stage別経路)は実装済み。
> 以下で `[x]` の項目はT-057で満たしている。本タスクは残りだけを持つ。
> なお1項目目の「ArtifactBase継承」「gen_models再生成」はいずれも実施していない。
> 前者は決定的producerが `confidence` / `created_by.skill` / `model` を供給できないため意図的に非継承
> (schemaのdescriptionと契約テストで固定)、後者はADR-0008で生成パイプライン自体が廃止済み。

- [x] `schemas/gate-decision.schema.json` が作成され(§6.24準拠。ArtifactBaseは上記の理由で非継承)、validator配線・pytestがpassする
- [x] gate評価の実行体(gate evaluator)が `policies/gate-policy.yaml` を読み、全gateを評価し、gateごとの判定(stage・outcome・理由)を含むGateDecisionを保存できる。**ただし評価対象はrun単位**であり、「対象runのartifact群」への展開は未着手
- [ ] block 4 gate(source grounding / oracle / evidence / security)は違反時に実際にblockし、変更対象のP0/P1に限定される(§17.4 grandfathering。block発火・非発火両方のテストで実証)。oracle gate(変更対象のP0/P1要求にOracleSpecなしをblock)のblock配線はここで行う(T-031の注記参照)
- [ ] security gateはPhase 1では入力が限定的(SecurityFinding生成skillが無いため、Tool Gateway audit logのpolicy violation等)。入力が未収集の場合の挙動を定義し(黙ってpass扱いにしない。inconclusive等)、テストで実証する。**注: 「未収集ならinconclusive、passにはしない」という一般則はT-057で定義・実証済み**(`test_gates_without_an_evaluator_are_inconclusive_not_pass`)。残るのはsecurity gate固有の入力(Tool Gateway audit log)を実際に読むruleの実装
- [ ] shadow gate群(change impact / test impact / coverage gap / reuse・dedup)は判定を記録するだけでblockしない(テストで実証)。各gateのstageが計画§6と `policies/gate-policy.yaml` で一致していることを確認する(stage変更の記帳はT-036 / T-043で実施済みの想定。残不整合があればここでCHANGELOG記帳のうえ揃える)。**注: shadow段階が判定に影響しないこと自体はT-057で実証済み**(`test_shadow_stage_failure_is_recorded_but_changes_nothing`)。残るのは各gateの実stageを計画§6へ揃えることとCHANGELOG記帳
- [x] stageをテストfixtureで差し替えた場合にwarn / block経路が実際に動くことをテストで実証する(§20完了条件「duplicate test candidateをblock/warnできる」の能力実証。実運用stageはshadowのまま)
- [ ] ReleaseReadinessReportのgate結果欄がGateDecision recordから生成されるようT-053の配線を更新する(暫定記録からの置き換え)
- [ ] shadow判定と人間の最終判断からgate_precision(§19.7)を算出できる集計スクリプトがあり、計測結果の記録先が `docs/knowledge/calibration/` に用意されている
- [ ] gate-policy.yaml変更時のCHANGELOG運用(計画§6)がREADMEに従って実施されている

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
