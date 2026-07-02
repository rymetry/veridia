---
task_id: T-008
epic: artifact-schema
plan_ref: phase-0-foundation.md#2-完了条件
status: not_started
owner:
blocked_by: [T-002, T-003, T-004, T-005, T-006, T-007]
---

# T-008: Artifact validator実装(source_refs必須化を含む)

## 目的

任意のartifact JSONを共通契約+個別schemaで検証する再利用可能なvalidator(lib + CLI)を実装する。計画§2完了条件「source_refsが空のartifactをvalidatorがrejectする」をカバーする。

## 参照

- 計画: §2 完了条件、§3 WS-A
- North Star: §6.1(source_refsが空のartifactはrelease gateに使えない)

## DoD

- [ ] validatorがartifact JSONを受け取り、artifact_typeに応じたschema検証を実行できる(CLIまたはlib呼び出しで確認)
- [ ] `source_refs` が空(または欠落)のartifactをrejectすることがテストで実証されている(計画§2完了条件)
- [ ] T-004〜T-007の有効サンプルすべてがvalidatorをpassする(テストで確認)
- [ ] reject時のエラーメッセージが原因field を特定できる形式である

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果、CLI実行例)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
