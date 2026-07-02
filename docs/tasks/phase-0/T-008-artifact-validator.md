---
task_id: T-008
epic: artifact-schema
plan_ref: phase-0-foundation.md#2-完了条件
status: done
owner:
blocked_by: [T-002, T-003, T-004, T-005, T-006, T-007]
---

# T-008: Artifact validator実装(source_refs必須化を含む)

## 目的

任意のartifact JSONを共通契約+個別schemaで検証する再利用可能なvalidator(lib + CLI)を実装する。計画§2完了条件「source_refsが空のartifactをvalidatorがrejectする」をカバーする。

## 参照

- 計画: §2 完了条件、§3 WS-A
- North Star: §6.1(source_refsが空のartifactはrelease gateに使えない)
- 申し送り(T-003から):
  - `models/`(生成Pydanticモデル)はpytest外の通常実行ではimport解決されない(`[tool.uv] package = false`)。validatorをlib+CLIとして実装する際にimport解決方式を決める([learning-log 2026-07-02 process-learningエントリ](../../knowledge/learning-log.md)参照。ADR-0002委任範囲を超える場合はADR)
  - `created_at` の `format: date-time` は生JSON検証では注釈のみ(naive datetimeが通る)。契約意図はtimezone必須(schema description参照)であり、生JSON側でformatを強制するか(jsonschemaのFormatChecker利用等)は本タスクで決める

## DoD

- [x] validatorがartifact JSONを受け取り、artifact_typeに応じたschema検証を実行できる(CLIまたはlib呼び出しで確認)
- [x] `source_refs` が空(または欠落)のartifactをrejectすることがテストで実証されている(計画§2完了条件)
- [x] T-004〜T-007の有効サンプルすべてがvalidatorをpassする(テストで確認)
- [x] reject時のエラーメッセージが原因field を特定できる形式である

## 検証方法・根拠

- lib API:
  - `tests/test_artifact_validator.py::test_validator_accepts_all_phase_0_artifact_samples` が、T-004〜T-007の7 artifact種(requirement_spec / risk_spec / oracle_spec / execution_evidence / test_asset_index / change_impact_spec / quality_analytics_snapshot / release_readiness_report)の有効サンプルを `validate_artifact()` で検証し、passすることを確認。
  - `tests/test_artifact_validator.py::test_validator_rejects_unknown_or_missing_artifact_type` が、未知の `artifact_type` と `artifact_type` 欠落を `$.artifact_type` のmachine-readable errorとしてrejectすることを確認。
- `source_refs`:
  - `tests/test_artifact_validator.py::test_validator_rejects_empty_or_missing_source_refs` が、空配列・欠落の両方を `$.source_refs` のerrorとしてrejectすることを確認(計画§2完了条件)。
- reject時のfield path:
  - `tests/test_artifact_validator.py::test_validation_error_exposes_serializable_details` が、`ArtifactValidationError.to_dict()` の `field_path` / `message` / `schema_path` / `validator` を確認。
  - `tests/test_artifact_validator.py::test_validator_rejects_naive_created_at_with_machine_readable_field_path` が、timezone無し `created_at` を `$.created_at` / `validator=format` でrejectすることを確認。
- CLI:
  - `tests/test_artifact_validator.py::test_cli_accepts_valid_artifact_file` と `tests/test_artifact_validator.py::test_cli_reports_field_path_for_invalid_artifact` で、CLI `main()` の成功/失敗コードとfield path出力を確認。
  - 実行例:
    - valid: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python -m artifact_validator /path/to/artifact.json` → `valid: /path/to/artifact.json`、exit 0
    - invalid JSON出力: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python -m artifact_validator --json /path/to/artifact.json` → `{"errors":[{"field_path":"$.source_refs", ... "validator":"minItems"}]}`、exit 1
- 申し送り対応方針:
  - `models/` import解決: validator runtimeは生成Pydanticモデルをimportせず、ADR-0002の正本である `schemas/*.schema.json` を直接読む。libはroot package `artifact_validator` として置き、CLIはrepo rootから `python -m artifact_validator` で起動する。`[tool.uv] package = false` は変更しない。T-009 / T-010 / T-013 は `from artifact_validator import validate_artifact` またはCLI呼び出しで利用できる。ADR-0002の「schema正本+生JSON contract検証」範囲内の具体化であり、新規ADRは不要。
  - `created_at` format強制: validatorでは `jsonschema.FormatChecker` にtimezone-aware `date-time` checkerを登録し、timezone無しdatetimeを生JSON側でもrejectする。理由は、North Star §6.1のrelease gate入力では生JSON validatorが境界になり、schema descriptionのtimezone必須意図と生成PydanticモデルのAwareDatetime側挙動に合わせるため。schema変更・依存追加は不要。
- 実行結果:
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_artifact_validator.py -q` → 16 passed
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest` → 423 passed
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff check .` → All checks passed
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff format --check .` → 25 files already formatted

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: [learning-log 2026-07-03 process-learning](../../knowledge/learning-log.md)
