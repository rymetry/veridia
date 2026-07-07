---
task_id: T-044
epic: quality-intelligence
plan_ref: phase-1-crud-mvp.md#4-canonical-workflowマッピング
status: not_started
owner:
blocked_by: [T-024]
---

# T-044: `performance-risk-detection` 事前準備(Stretch)

## 目的

Phase 4(Performance Skill導入)開始前の棚卸しとして、PR差分から検出すべき性能リスク観点(N+1、重いquery、外部API待ち等)を対象サービスの実情に即して整理する(W13、Stretch)。**Phase 1のrelease gate必須条件にはしない**(計画§4)。skill実装はPhase 4で行い、ここでは観点カタログの整備まで。

## 参照

- 計画: §4(W13はStretch)、§7
- North Star: §14.3(Performance risk catalog)、§21 Week 3(事前準備のDoD)、§6.19(PerformanceRiskSpec — schema定義はPhase 4)

## DoD

- [ ] §14.3のcatalogを起点に、対象サービスで実際に起こり得る性能リスク観点が棚卸しされ、`docs/domain/` 配下(対象サービスのファイル)に記録されている
- [ ] 対象repoの実PR 1件以上に対して観点を手動適用し、検出できた/できなかった観点の記録が `docs/knowledge/learning-log.md` にある(Phase 4のskill設計の入力)
- [ ] ReleaseReadinessReportやgateへの配線は行っていない(参考情報扱い。計画§4の制約を守る)

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
