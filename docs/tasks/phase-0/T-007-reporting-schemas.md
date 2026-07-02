---
task_id: T-007
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-003]
---

# T-007: 基盤spec schema定義(QualityAnalyticsSnapshot / ReleaseReadinessReport)

## 目的

Reporting Foundationの2 artifactのJSON Schemaを定義する。計画§2完了条件「ReleaseReadinessReportのschemaがvalidationを通る」をカバーする。

## 参照

- 計画: §2 完了条件、§3 WS-A
- North Star: §6.17(QualityAnalyticsSnapshot)、§6.18(ReleaseReadinessReport)

## DoD

- [ ] `schemas/quality-analytics-snapshot.schema.json` / `release-readiness-report.schema.json` が存在し、`allOf` でartifact-baseを継承している
- [ ] QualityAnalyticsSnapshotがcoverage / execution / evidence / costを集約できる(サンプルinstanceで確認)
- [ ] ReleaseReadinessReportがpass/warn/block・理由・evidence_refsを表現でき、有効サンプルinstanceがschema validationを通る(テストで実証。計画§2完了条件)
- [ ] 各schemaについて、不正サンプルがfailするテストがある

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
