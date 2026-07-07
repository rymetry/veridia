---
task_id: T-041
epic: quality-intelligence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-027, T-031]
---

# T-041: `change-impact-analysis` skill(W3: 意味的マッピング)

## 目的

PR差分から影響を受けるcomponent・要求・リスク・APIを特定するChangeImpactSpecを生成するskillを実装する(W3)。Phase 0 T-010は決定的な候補生成(file→component推定)まで。本タスクで要求・リスクへの意味的マッピングをLLM skill化し、Phase 1完了条件「ChangeImpactSpecを生成できる」を実対象で満たす。

## 参照

- 計画: §5(quality-intelligence)
- North Star: §7.4(change-impact-analysis)、§6.9(ChangeImpactSpec)、§12.3(Quality Intelligence workflow)、§12.5(決定的フロア: LLM出力が決定的解析結果を狭めない)
- Phase 0: T-010(候補generator。再利用する)

## DoD

- [ ] `qa-skills/change-impact-analysis/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] T-010の決定的generatorの出力を下限(floor)とし、LLMがreview済み要求・リスクへのマッピングを追加する構成になっている — LLMの出力が決定的解析の影響範囲を削れない(§12.5。テストで実証)
- [ ] skill runner経由で、対象repoの実PRからChangeImpactSpec(影響component・requirement・risk・API)を生成できる(実行記録あり、validator pass)
- [ ] `evals/` にpositive / negative caseがあり、fake LLMでの構造検証がpytestでpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
