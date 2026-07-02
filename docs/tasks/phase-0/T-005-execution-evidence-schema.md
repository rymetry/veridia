---
task_id: T-005
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-003]
---

# T-005: ExecutionEvidence schema定義

## 目的

Evidence Store(WS-B)が保存する実行証跡の契約を定義する。WS-Bはこのschemaに依存するため、コアspecとは別タスクとして先行完了できるようにする。

## 参照

- 計画: §3 WS-A、§4(WS-BがExecutionEvidence schemaに依存)
- North Star: §6.23(ExecutionEvidence)、§15.3(Evidence Storeの保存対象)

## DoD

- [ ] `schemas/execution-evidence.schema.json` が存在し、`allOf` でartifact-baseを継承している
- [ ] test実行結果・state diff・logsへの参照を表現できる(§6.23のfield構成に準拠)
- [ ] 有効サンプルがpassし、不正サンプルがfailするテストがある

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
