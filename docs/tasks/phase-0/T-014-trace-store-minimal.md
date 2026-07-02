---
task_id: T-014
epic: evidence-trace-store
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-011, T-012]
---

# T-014: Trace Store最小版(trace record保存・参照)

## 目的

agent実行過程の記録先となるTrace Store最小版を実装する。Tool Gatewayのaudit log(T-016)の保存先。Evidence Storeとは保存対象を分ける(§15.1)。

## 参照

- 計画: §3 WS-B
- North Star: §15.1 / §15.2(保存対象のうちPhase 0はtool call / error / run metricsの最小subset)

## DoD

- [ ] trace record(最低限: tool call、error)をrun_id / trace_id付きで保存し、trace_idまたはrun_idを指定して関連recordを時系列で照会できることが統合テストで実証されている
- [ ] §15.2のうちPhase 0で保存しない対象(handoff / guardrail / QI event等)がREADMEにスコープ外として明記されている

## 検証方法・根拠

(完了時に記入。想定: 統合テストの実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
