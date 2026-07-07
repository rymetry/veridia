---
task_id: T-036
epic: test-asset-reuse
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-033, T-034]
---

# T-036: `duplicate-test-detection` skill + dedup gate(shadow)配線

## 目的

新規テスト生成候補と既存テストの重複を検出しDuplicateTestReportを生成するskillを実装する(W5後半)。dedup gateはshadowとして配線し、precision計測を開始する(計画§6)。Phase 1完了条件「duplicate test candidateをblock/warnできる」をカバーする(初期はshadow/warn。blockへの昇格は計画§6の昇格条件に従う)。

## 参照

- 計画: §5(test-asset-reuse)、§6(shadow開始gateにreuse・dedup系を含む)
- North Star: §7.4(duplicate-test-detection)、§6.15(DuplicateTestReport)、§13.4(Dedup gate閾値)、§19.7(gate precision)

## DoD

- [ ] `qa-skills/duplicate-test-detection/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] テスト意図または生成候補とTestAssetIndexを入力に、類似度スコア付きDuplicateTestReportを生成できる(決定的な類似度算出を優先し、LLM判定を使う場合は候補提示に留める。実行記録あり)
- [ ] `policies/gate-policy.yaml` の `reuse_dedup` gateのstageを計画§6(shadow開始)と整合させる(Phase 0時点のpolicyは `warn` のため `shadow` へ変更し、policy version更新とCHANGELOG記帳を行う)
- [ ] dedup gateがshadow段階として発火し、判定結果(would_block / would_warn)が記録される — 実際にはblockしない(テストで実証)
- [ ] shadow判定の記録から§19.7のgate_precision算出に必要なデータ(判定と人間の最終判断の対応)が取れる形になっている
- [ ] `evals/` にpositive(明確な重複)/ negative(似て非なるテスト)caseがあり、pytestがpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
