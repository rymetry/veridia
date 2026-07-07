---
task_id: T-039
epic: modeling-generation
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-031, T-037]
---

# T-039: `testability-analysis` skill(W8: TestabilityReport)

## 目的

対象機能の観測可能性・制御可能性・リセット可能性を評価しTestabilityReportを生成するskillを実装する(W8)。sandbox統合(T-047)とstate diff capture(T-049)で「どこを観測すべきか」の入力になる。

## 参照

- 計画: §5(modeling-generation)
- North Star: §7.3(testability-analysis)、§6.8(TestabilityReport)

## DoD

- [ ] `qa-skills/testability-analysis/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] skill runner経由で、review済みRequirementSpecと対象のアーキテクチャ情報を入力に、TestabilityReport候補(観測点 / 制御点 / reset blocker)を生成できる(実行記録あり)
- [ ] 生成物がartifact_validatorをpassし、対象機能のDB / API / event / logの観測点が具体的に列挙されている(T-047・T-049がこのreportを参照して実装に入れる水準)
- [ ] `evals/` にpositive / negative caseがあり、fake LLMでの構造検証がpytestでpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
