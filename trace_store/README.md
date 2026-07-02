# Trace Store

T-014のPhase 0最小Trace Store。agent実行過程のうち、redaction済みの `tool_call` / `error` / `run_metrics` recordだけをSQLiteへ保存する。

## ローカル起動

追加サービスは不要。PostgreSQL、OpenTelemetry collector、Docker、cloud credentialは使わない。

```bash
uv sync --group dev
uv run pytest tests/test_trace_store.py
```

デフォルトのstore rootはリポジトリルート相対の `.veridia/store/trace/`。

```text
.veridia/store/trace/
  trace.sqlite3
```

pytestでは必ず `tmp_path` などの一時ディレクトリを渡す。

```python
from trace_store import TraceStore

store = TraceStore.open(tmp_path / "trace")
record = store.save_record(
    trace_context,
    sequence=1,
    event_type="tool_call",
    name="tool.orders.cancel",
    status="ok",
    started_at="2026-07-03T12:34:56Z",
    ended_at="2026-07-03T12:34:56Z",
    latency_ms=25,
    redacted_args={"order_id": "<redacted>"},
    result_summary="cancelled one synthetic order fixture",
)
by_trace = store.find_by_trace_id(record.trace_id)
by_run = store.find_by_run_id(record.run_id)
```

`TraceStore.open()` の引数を省略すると `.veridia/store/trace/` が作られるため、テストでは省略しない。

## 保存構造

- metadata DB: `<store_root>/trace.sqlite3`
- Evidence Storeとは別DB file、別APIにする
- blob storeは持たない
- 照会API: `find_by_trace_id(trace_id)` / `find_by_run_id(run_id)`
- 照会順: `sequence`、`started_at`、`span_id`

trace recordには `run_id` / `trace_id` / `span_id` / `parent_span_id` / `sequence` / `event_type` / `name` / `status` / `started_at` / `ended_at` / `latency_ms` / `redacted_args` / `result_summary` / `error_summary` を保存する。

SQLite実装はADR-0003のPhase 0 adapterであり、DDL / DMLはSQLite固有の `AUTOINCREMENT`、SQLite関数、SQLite固有のconflict構文に依存しない。保存APIはraw args / raw resultを受け取らず、呼び出し側でredaction済みの `redacted_args` とsummaryだけを渡す。

## Phase 0の保存対象

North Star §15.2のうち、Phase 0で保存するevent typeは次に限定する。

- `tool_call`
- `error`
- `run_metrics`

次の対象はPhase 0のTrace Storeでは保存しない。

- agent event
- handoff
- guardrail
- model config
- transcript
- skill event
- QI event

Tool Gateway audit log(T-016)は、gateway呼び出しごとに `TraceContext` からchild contextを作り、`tool_call` recordとしてこのTrace Storeへ保存する想定。

## 保存禁止対象

North Star §15.4に従い、次はTrace Storeへ保存しない。

- raw tool args
- raw tool result
- raw secret / token
- 不要なPII
- raw production data
- private chain-of-thought
- policy上保存不可の会話
- 外部著作物の過剰保存

Phase 0のTrace Storeは機械的なsecret / PII / production data検出を行わない。保存APIに渡す `redacted_args`、`result_summary`、`error_summary` は、呼び出し側でredaction済みであることを前提にする。
