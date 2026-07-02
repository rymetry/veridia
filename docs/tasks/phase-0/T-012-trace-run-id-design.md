---
task_id: T-012
epic: evidence-trace-store
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
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

- ID形式・採番・伝播規則:
  - 設計文書: [trace_id / run_id ID設計(T-012)](../../plan/trace-run-id-design.md)
  - 内容: `run_id` / `trace_id` / `span_id` / `parent_span_id` の形式、UTC時刻prefix + `secrets.token_hex` suffixの採番、run → trace → artifact / tool callへの伝播規則を文書化。
  - ADR要否: ADR-0003のOpenTelemetry寄り命名・span親子関係を具体化する範囲であり、North Star / ADR-0002 / ADR-0003からの逸脱はないため追加ADRなし。
- ID生成ユーティリティ:
  - 実装: `trace_ids/`
  - テスト: `tests/test_trace_ids.py`
  - 検証結果: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_trace_ids.py -q` → `5 passed`
  - 全体検証: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest` → `434 passed`
- ArtifactBase `trace_id` との整合:
  - `schemas/artifact-base.schema.json` の `trace_id` は `type: string`、`minLength: 1`、pattern未定義。生成値 `trace-YYYYMMDD-<16 lowercase hex>` はschemaを満たす。
  - 既存example `trace-20260702-0001` と同じ `trace-<UTC日付>-<suffix>` 構造を維持し、suffixは衝突耐性のため16 hex文字に拡張。
  - テスト: `tests/test_trace_ids.py::test_generated_trace_id_passes_artifact_base_schema_validation`
- lint / format:
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff check .` → `All checks passed!`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff format --check .` → `40 files already formatted`

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
