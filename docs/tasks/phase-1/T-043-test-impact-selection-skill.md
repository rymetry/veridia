---
task_id: T-043
epic: quality-intelligence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-034, T-040, T-041]
---

# T-043: `test-impact-selection` skill(W11: TestImpactPlan生成)

## 目的

ChangeImpactSpecとTestAssetIndexから、実行推奨テストとskip候補(理由付き)を選択しTestImpactPlanを生成するskillを実装する(W11)。Phase 1完了条件「TestImpactPlanを生成できる」をカバーする。

## 参照

- 計画: §5(quality-intelligence)、§6(test impact gateはshadow開始)
- North Star: §7.4(test-impact-selection)、§6.10(TestImpactPlan)、§12.4(Test Impact Selection方針)、§12.5(決定的フロア)

## DoD

- [ ] `qa-skills/test-impact-selection/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] skill runner経由で、対象repoの実PRのChangeImpactSpecとTestAssetIndexを入力に、TestImpactPlan(must_run / recommended / skip候補、各理由とevidence参照付き)を生成できる(実行記録あり、validator pass)
- [ ] 選択方針が§12.4に従う(判断がつかない変更は実行側に倒す)ことがSKILL.mdに明記され、evals case(影響不明の変更→skipしない)で検証されている
- [ ] §12.5の決定的フロアを実装する: skip判断には決定的evidence(coverage map / dependency graph等)を必須とし、LLM推論のみを根拠にskipしない。security testをskip対象にしない(テストで実証)
- [ ] `policies/gate-policy.yaml` の `test_impact` gateのstageを計画§6(shadow開始)と整合させる(Phase 0時点のpolicyは `warn` のため `shadow` へ変更し、policy version更新とCHANGELOG記帳を行う。`change_impact` gateも同様にここで揃える)
- [ ] test impact gate(high-risk変更でTestImpactPlanなし)がshadowとして判定を記録する(計画§6)
- [ ] fake LLMでの構造検証がpytestでpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
