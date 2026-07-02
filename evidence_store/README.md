# Evidence Store

T-013のPhase 0最小Evidence Store。ExecutionEvidenceをvalidatorで検証し、metadataをSQLiteへ、test result / state diff / log / payload blobをlocal filesystemへ保存する。

## ローカル起動

追加サービスは不要。PostgreSQL、MinIO、Docker、cloud credentialは使わない。

```bash
uv sync --group dev
uv run pytest tests/test_evidence_store.py
```

デフォルトのstore rootはリポジトリルート相対の `.veridia/store/evidence/`。

```text
.veridia/store/evidence/
  evidence.sqlite3
  objects/
```

pytestでは必ず `tmp_path` などの一時ディレクトリを渡す。

```python
from evidence_store import EvidenceStore

store = EvidenceStore.open(tmp_path / "evidence")
stored = store.save_execution_evidence(
    artifact,
    test_result={"summary": {"passed": 3, "failed": 0}},
    state_diff={"tables": [{"name": "orders", "rows_changed": 1}]},
    logs={"test-runner.log": b"3 passed\n"},
)
same = store.get_by_artifact_id(stored.metadata.artifact_id)
by_trace = store.find_by_trace_id(stored.metadata.trace_id)
```

`EvidenceStore.open()` の引数を省略すると `.veridia/store/evidence/` が作られるため、テストでは省略しない。

## 保存構造

- metadata DB: `<store_root>/evidence.sqlite3`
- object root: `<store_root>/objects/`
- logical ref: `object-storage://evidence/<run_id>/<object_name>`
- blob adapter interface: `put(run_id, object_name, data)` / `get(logical_ref)` / `list(run_id)`

metadataには `artifact_id` / `trace_id` / `run_id` / `test_asset_id` / `verdict` / `created_at` / `schema_version` / `payload_ref` / `state_diff_ref` / `log_refs` を保存する。読み出しAPIは `artifact_id`、`trace_id`、`run_id`、`test_asset_id` の検索を提供する。

SQLite実装はADR-0003のPhase 0 adapterであり、DDL / DMLはSQLite固有の `AUTOINCREMENT`、SQLite関数、SQLite固有のconflict構文に依存しない。local absolute pathはmetadataに保存せず、blobはlogical ref経由で読む。

## 保存禁止対象

North Star §15.4に従い、次はEvidence Storeへ保存しない。

- raw secret / token
- 不要なPII
- raw production data
- private chain-of-thought
- policy上保存不可の会話
- 外部著作物の過剰保存

Phase 0のEvidence Storeは機械的なsecret / PII / production data検出を行わない。保存APIに渡す `artifact`、`test_result`、`state_diff`、`logs` は、呼び出し側でredaction済みであることを前提にする。この制約は `docs/knowledge/learning-log.md` にT-013の課題として記録している。
