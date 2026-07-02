---
task_id: T-012
epic: evidence-trace-store
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-002, T-003]
---

# T-012: trace_id / run_id設計と生成ユーティリティ

## 目的

全artifactと実行をtrace可能にするID体系(形式、採番、伝播規則)を設計し、生成ユーティリティを実装する。WS-Bのstore実装とWS-Cのaudit logの前提。

## 参照

- 計画: §3 WS-B
- North Star: §15.1 / §15.2、§6.1(ArtifactBaseのtrace_id field)

## DoD

- [ ] ID形式・採番・伝播規則(run → trace → artifact / tool callへの付与点)が文書化されている(設計判断を伴う場合はADR、そうでなければ実装リポジトリ内のdesign doc)
- [ ] ID生成ユーティリティが実装され、形式・一意性がテストで検証されている
- [ ] ArtifactBase(T-003)の `trace_id` fieldと形式が整合している(schemaのpattern等で確認)

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果、設計文書へのリンク)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
