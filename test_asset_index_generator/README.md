# TestAssetIndex generator

T-009のPhase 0最小generator。対象repoの `tests/` 配下にあるpytestファイル
(`test_*.py` / `*_test.py`)を走査し、`test_asset_index` artifact JSONを生成する。
LLMは使わず、path昇順の決定的な出力にする。

```bash
uv run python -m test_asset_index_generator . /tmp/test-asset-index.json
uv run python -m artifact_validator /tmp/test-asset-index.json
```

## Phase 0で未収集のfield

Phase 0ではテストファイルの存在、repo内path、pytest由来のtest_typeだけを収集する。
Requirement / Risk / Oracleとの紐付け、flake履歴、最終成功・失敗時刻はまだ収集しない。

- `covered_requirements`: 空配列。未収集または該当なしを表す。
- `covered_risks`: 空配列。未収集または該当なしを表す。
- `oracle_refs`: 空配列。未収集または該当なしを表す。
- `stability.flake_rate`: `null`。flake履歴未収集を表す。
- `stability.last_failed_at`: `null`。未失敗または不明を表す。
- `stability.last_passed_at`: `null`。未成功または不明を表す。

生成物には補助metadataとして `collection_status` を入れ、Phase 0未収集であることを
機械的にも確認できるようにする。

## 決定性

デフォルトの `created_at` / `indexed_at` は `1970-01-01T00:00:00Z` に固定する。
実運用の生成時刻を記録したい場合は `--generated-at` で明示する。artifact IDはrepo名、branch、
生成時刻、検出したasset pathのsha256から生成する。`trace_id` は `trace-YYYYMMDD-<16hex>` 形式で、
date部は `generated_at` の日付、hex部は同じ入力fingerprintの安定hashから作る。
