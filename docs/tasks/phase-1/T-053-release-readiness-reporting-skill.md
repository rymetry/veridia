---
task_id: T-053
epic: reporting-gate
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-052]
---

# T-053: `release-readiness-reporting`(W17: ReleaseReadinessReport生成)

## 目的

QualityAnalyticsSnapshot等からReleaseReadinessReport(pass / warn / block、理由、evidence_refs)を生成し、Markdown/HTMLで出力する(W17)。Phase 1完了条件「ReleaseReadinessReportを出せる」をカバーする。schemaはPhase 0 T-007で定義済み。

## 参照

- 計画: §5(reporting-gate)
- North Star: §7.4(release-readiness-reporting)、§6.18(ReleaseReadinessReport)、§21 Week 4(Markdown/HTML出力のDoD)

## DoD

- [ ] QualityAnalyticsSnapshotとgate判定記録を入力に、ReleaseReadinessReport(JSON)を生成できる(validator pass)。判定(pass / warn / block)は決定的ロジックで算出し、LLMは説明文生成のみに使う(判定を変えない)。この時点のgate判定入力はT-031等の暫定記録でよい(GateDecision schema化後の再配線はT-054で行う)
- [ ] 同reportをMarkdownまたはHTMLとして人間可読形式で出力できる(§21 Week 4のDoD)
- [ ] reportにChangeImpact / TestImpact / CoverageGap / Reuse・Dedup結果が表示される(§21 Week 4「Gate Report拡張」の表示範囲。PerformanceRiskは表示しない — Phase 4以降)
- [ ] すべての判定理由がevidence_refsから根拠へ辿れる(サンプルreportで1判定以上を実際に辿って確認)
- [ ] 対象repoの実PR 1件で生成した記録がある
- [ ] `uv run pytest` がpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
