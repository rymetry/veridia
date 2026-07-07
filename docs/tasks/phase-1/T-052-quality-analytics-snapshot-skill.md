---
task_id: T-052
epic: reporting-gate
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-048]
---

# T-052: `quality-analytics-snapshot`(W16: 品質状態の集約)

## 目的

実行結果・coverage・gap・costを集約したQualityAnalyticsSnapshotを生成する(W16)。ReleaseReadinessReport(T-053)とDashboard(T-055)の入力になる。schemaはPhase 0 T-007で定義済み。

## 参照

- 計画: §5(reporting-gate)
- North Star: §7.4(quality-analytics-snapshot)、§6.17(QualityAnalyticsSnapshot)、§5.8(Quality Analytics & Release Reporting)

## DoD

- [ ] 対象PR(またはrun)のartifact群(ExecutionEvidence、CoverageGap、TestImpactPlan、reuse/dedup結果)とLLMコスト記録(ADR-0005の記録先)を集約し、QualityAnalyticsSnapshotを生成できる(決定的集約を基本とし、LLM要約は使う場合も数値を改変しない)
- [ ] 生成物がartifact_validatorをpassし、集約元への参照(evidence_refs等)から数値の根拠を辿れる
- [ ] 入力artifactが欠けている場合、欠損として明示され黙って0扱いにならない(テストで実証)
- [ ] 対象repoの実PR 1件で生成した記録がある
- [ ] `uv run pytest` がpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
