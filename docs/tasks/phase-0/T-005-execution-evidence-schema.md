---
task_id: T-005
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-003]
---

# T-005: ExecutionEvidence schema定義

## 目的

Evidence Store(WS-B)が保存する実行証跡の契約を定義する。WS-Bはこのschemaに依存するため、コアspecとは別タスクとして先行完了できるようにする。

## 参照

- 計画: §3 WS-A、§4(WS-BがExecutionEvidence schemaに依存)
- North Star: §6.23(ExecutionEvidence)、§15.3(Evidence Storeの保存対象)

## DoD

- [ ] `schemas/execution-evidence.schema.json` が存在し、`allOf` でartifact-baseを継承している
- [ ] test実行結果・state diff・logsへの参照を表現できる(§6.23のfield構成に準拠)
- [ ] 有効サンプルがpassし、不正サンプルがfailするテストがある

## 検証方法・根拠

- DoD 1: `schemas/execution-evidence.schema.json` を追加し、`allOf` に `artifact-base.schema.json` への `$ref` が含まれることを `tests/test_execution_evidence_schema.py::TestSchemaItself::test_inherits_artifact_base_via_allof` で確認した。
- DoD 2: §6.23のfield構成に合わせて `run_id` / `test_asset_id` / `environment` / `inputs` / `outputs` / `state_before` / `state_after` / `state_diff` / `tool_calls` / `logs` / `screenshots` / `grader_results` / `verdict` / `reproduction_bundle` を定義した。`outputs.test_result_ref`、`state_diff.ref`、`logs[].ref` を含む有効サンプルが `tests/test_execution_evidence_schema.py` でpassすることを確認した。
- DoD 3: 有効サンプルpass、不正サンプルfailを `tests/test_execution_evidence_schema.py` に追加した。主な不正ケースは必須field欠落、未知の `verdict`、`environment.env_id` 欠落、payload fieldの型不一致、`logs[].ref` 欠落、`grader_results[].verdict` 欠落。
- 生成物: `uv run python scripts/gen_models.py` で `models/execution_evidence_schema.py` を生成し、`uv run python scripts/gen_models.py --check` でschemaとmodelsの差分なしを確認した。
- 検証結果(2026-07-02): `uv run pytest` → 267 passed、`uv run ruff check .` → All checks passed、`uv run ruff format --check .` → 16 files already formatted、`uv run python scripts/gen_models.py --check` → models は schemas の再生成結果と一致。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
