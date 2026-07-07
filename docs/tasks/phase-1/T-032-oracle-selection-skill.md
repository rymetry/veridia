---
task_id: T-032
epic: grounding-oracle
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-030, T-031]
---

# T-032: `oracle-selection` skill(W7: P0/P1要求へOracleSpec候補付与)

## 目的

review済みRequirementSpec / RiskSpecを入力に、判定方式を定めるOracleSpec候補を生成するskillを実装する(W7)。Phase 1完了条件「P0/P1要求にOracleSpecを付与できる」をカバーする。

## 参照

- 計画: §5(grounding-oracle)
- North Star: §7.3(oracle-selection)、§6.6(OracleSpec)、§9.2〜9.3(Oracle分類・優先順位: deterministic oracle優先)

## DoD

- [ ] `qa-skills/oracle-selection/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] skill runner経由で、review済み(T-031のフローで承認済み)のP0/P1要求すべてにOracleSpec候補を付与できる(対象PRでの実行記録: P0/P1要求数 = OracleSpec候補数)
- [ ] oracle種別の選択が§9.3の優先順位(deterministicが使える箇所でAI judgeを選ばない)に従うことがSKILL.mdに明記され、evals caseで検証されている
- [ ] 生成OracleSpecがartifact_validatorをpassする(`status: draft` + `requires_human_review: true` で保存され、T-031のフローでreviewされる)
- [ ] `evals/` にpositive / negative caseがあり、fake LLMでの構造検証がpytestでpassする

## 検証方法・根拠

<完了時に記入: 実行記録、テスト結果>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
