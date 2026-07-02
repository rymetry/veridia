---
task_id: T-003
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-001, T-002]
---

# T-003: ArtifactBase JSON Schema定義

## 目的

全artifact schemaが継承する共通契約(ArtifactBase)を定義する。WS-Aの他schemaタスクすべての前提。

## 参照

- 計画: §3 WS-A
- North Star: §6.1(共通必須field一覧と継承方式)
- `schemas/README.md`(命名・継承ルール)

## DoD

- [ ] `schemas/artifact-base.schema.json` が存在し、§6.1に列挙された共通必須fieldすべてを必須として定義している(schemaの `required` 配列と§6.1の列挙との一致をレビューで確認。field一覧はここに複製しない: AGENTS.md変更ルール2)
- [ ] schema自体がJSON Schema meta-schemaに対してvalid(テストで検証)
- [ ] 有効なサンプルinstanceがpassし、必須field欠落サンプルがfailするテストがある

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
