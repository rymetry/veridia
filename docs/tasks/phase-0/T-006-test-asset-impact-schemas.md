---
task_id: T-006
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-003]
---

# T-006: 基盤spec schema定義(TestAssetIndex / ChangeImpactSpec)

## 目的

Test Asset Foundation / Quality Intelligence Foundationの入口となる2 artifactのJSON Schemaを定義する。T-009 / T-010のgeneratorの出力契約。

## 参照

- 計画: §3 WS-A
- North Star: §6.13(TestAssetIndex)、§6.9(ChangeImpactSpec)

## DoD

- [ ] `schemas/test-asset-index.schema.json` / `change-impact-spec.schema.json` が存在し、`allOf` でartifact-baseを継承している
- [ ] TestAssetIndexが既存テストのpath / type / covered requirement・risk / oracle / flake rateを保持できる(§21 Week 1のDoD準拠。サンプルinstanceで確認)
- [ ] ChangeImpactSpecが影響component / requirement / risk / APIを保持できる(サンプルinstanceで確認)
- [ ] 各schemaについて、有効サンプルがpassし、不正サンプルがfailするテストがある

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
