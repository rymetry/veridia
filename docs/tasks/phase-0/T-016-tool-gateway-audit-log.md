---
task_id: T-016
epic: tool-gateway
plan_ref: phase-0-foundation.md#2-完了条件
status: done
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

- 統合テスト:
  - `tests/test_tool_gateway_audit.py::test_gateway_tool_call_is_saved_with_trace_id_and_redacted_args`
    - Gateway経由のtool callで `event_type="tool_call"` のaudit recordがTrace Storeへ保存されることを確認。
    - `run_id` / `trace_id` が親 `TraceContext` と一致し、`span_id` はchild span、`parent_span_id` は親spanであることを確認。
    - `name` / `redacted_args` / `result_summary` / `status` / `latency_ms` を確認。
  - `tests/test_tool_gateway_audit.py::test_redacts_secret_like_argument_keys_recursively`
    - `token` / `secret` / `password` / `api_key` / `authorization` 系keyの値がnested dict/listでも `"<redacted>"` へmaskされることを確認。
  - `tests/test_tool_gateway_audit.py::test_rejected_tool_call_is_saved_with_error_status`
    - allowlist外のtool callでも `status="error"`、`error_summary` 付きのaudit recordが保存され、例外が再送出されることを確認。
  - `tests/test_tool_gateway_audit.py::test_multiple_tool_calls_share_run_trace_and_record_child_spans`
    - 複数tool callが同一 `run_id` / `trace_id` を共有し、各tool callに別child spanと親 `parent_span_id` が保存されることを確認。
- 実行結果:
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest` -> `447 passed`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff check .` -> `All checks passed!`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff format --check .` -> `62 files already formatted`
- audit recordサンプル(redacted):

```json
{
  "run_id": "run-20260703T123456789012Z-000000000001",
  "trace_id": "trace-20260703-0000000000000002",
  "span_id": "0000000000000004",
  "parent_span_id": "0000000000000003",
  "sequence": 1,
  "event_type": "tool_call",
  "name": "fixture.echo",
  "status": "success",
  "latency_ms": 0,
  "redacted_args": {
    "message": "hello",
    "api_token": "<redacted>",
    "metadata": {
      "password": "<redacted>",
      "safe": "visible"
    }
  },
  "result_summary": "object keys=[message, ok] field_count=2",
  "error_summary": null
}
```

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
