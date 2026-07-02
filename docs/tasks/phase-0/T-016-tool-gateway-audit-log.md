---
task_id: T-016
epic: tool-gateway
plan_ref: phase-0-foundation.md#2-完了条件
status: not_started
owner:
blocked_by: [T-014, T-015]
---

# T-016: Tool Gateway audit log(trace_id付きtool call保存)

## 目的

Gateway経由の全tool callをTrace Storeへ記録する。計画§2完了条件「tool callがtrace_id付きで保存される」をカバーする。

## 参照

- 計画: §2 完了条件、§3 WS-C
- North Star: §5.6(Audit log)、§15.2(tool call: name、args redacted、result summary、status)

## DoD

- [ ] Gateway経由のtool call実行時に、audit recordがtrace_id付きでTrace Storeへ保存されることが統合テストで実証されている(計画§2完了条件)
- [ ] audit recordにtool name / args(redacted) / result summary / status / 実行時間が含まれる(§15.2および§5.6 Audit log準拠。record内容をテストで確認)
- [ ] argsのredaction方針(最低限: secretパターンのマスク)が実装され、テストで確認されている

## 検証方法・根拠

(完了時に記入。想定: 統合テストの実行結果とaudit recordのサンプル)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
