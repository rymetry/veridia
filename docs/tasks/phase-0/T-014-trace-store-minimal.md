---
task_id: T-014
epic: evidence-trace-store
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
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

- DoD 1(trace record保存・trace_id/run_id照会):
  - `tests/test_trace_store.py::test_save_tool_call_and_error_records_then_query_in_chronological_order`
  - `tool_call` / `error` recordを同一 `run_id` / `trace_id` 付きで保存し、`find_by_trace_id` / `find_by_run_id` の両方が `sequence` / `started_at` 順で返すことを検証。
  - Evidence Storeとは別DB fileとして `<tmp_path>/trace/trace.sqlite3` が作られ、`evidence.sqlite3` が作られないことも検証。
- DoD 1(Phase 0対象外event_typeの拒否):
  - `tests/test_trace_store.py::test_rejects_event_types_outside_phase_0_subset`
  - `handoff` が `InvalidTraceEventTypeError` で拒否され、recordが保存されないことを検証。
- DoD 2(Phase 0で保存しない対象のREADME明記):
  - `trace_store/README.md` にNorth Star §15.2のうちPhase 0保存対象を `tool_call` / `error` / `run_metrics` に限定し、`agent event` / `handoff` / `guardrail` / `model config` / `transcript` / `skill event` / `QI event` をスコープ外として明記。
- 実行結果:
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run pytest` → 439 passed
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run ruff check .` → All checks passed
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run ruff format --check .` → 52 files already formatted

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
