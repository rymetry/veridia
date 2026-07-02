---
task_id: T-004
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-003]
---

# T-004: コアspec schema定義(RequirementSpec / RiskSpec / OracleSpec)

## 目的

Phase 1のagent/skillが入出力に使うコア3 artifactのJSON Schemaを定義する。

## 参照

- 計画: §3 WS-A
- North Star: §6.3(RequirementSpec)、§6.4(RiskSpec)、§6.6(OracleSpec)

## DoD

- [ ] `schemas/requirement-spec.schema.json` / `risk-spec.schema.json` / `oracle-spec.schema.json` が存在し、`allOf` でartifact-baseを継承している
- [ ] 各schemaについて、有効サンプルがpassし、domain固有必須field欠落サンプルがfailするテストがある

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
