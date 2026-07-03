---
task_id: T-010
epic: artifact-schema
plan_ref: phase-0-foundation.md#2-完了条件
status: done
owner:
blocked_by: [T-006, T-008]
---

# T-010: ChangeImpactSpec候補generator最小版

## 目的

PR diff(git diff)から候補レベルのChangeImpactSpecを生成する。計画§2完了条件「PR diffからChangeImpactSpec(候補レベル)を生成できる」をカバーする。LLM不使用の決定的実装(計画§1のスコープ。§12.5の実装方式が定める決定的な土台に相当する部分のみで、LLMによる意味的マッピング補完はPhase 1以降)。

## 参照

- 計画: §2 完了条件
- North Star: §6.9、§12.5(実装方式と決定的フロア)

## DoD

- [x] git diff(またはPR diff相当の入力)から、影響ファイル・componentの候補を含むChangeImpactSpec JSONを生成できる(サンプルdiffで実行して確認)
- [x] 生成物がT-008 validatorをpassする(テストで実証)
- [x] 候補レベルであること(requirement / riskへのマッピングはPhase 1以降)がconfidence等のfieldまたはREADMEで明示されている

## 検証方法・根拠

- サンプルdiff: `tests/fixtures/change_impact/sample.diff`
- 生成コマンド:

  ```bash
  UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python -m change_impact_generator tests/fixtures/change_impact/sample.diff /tmp/veridia-change-impact-spec.json --source-ref fixture://sample-pr
  ```

  結果: `generated: /tmp/veridia-change-impact-spec.json`

- validator:

  ```bash
  UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python -m artifact_validator /tmp/veridia-change-impact-spec.json
  ```

  結果: `valid: /tmp/veridia-change-impact-spec.json`

- pytest:

  ```bash
  UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_change_impact_generator.py -q
  ```

  結果: `3 passed`

- DoD根拠:
  - `test_cli_generates_valid_change_impact_spec_from_sample_diff`: CLI 1コマンドでsample diffから`change_impact_spec`を生成し、`validate_artifact`をpassすることを確認。
  - `test_generator_includes_file_and_component_candidates`: `changed_files`に`src/order/cancel_order.py` / `qa-skills/payments/README.md`、`changed_components`に`order` / `qa-skills/payments`が含まれることを確認。`impacted_requirements` / `impacted_risks` / `impacted_apis`はPhase 0未収集として空配列。
  - `test_generator_is_deterministic_for_same_input`: 同一diffと同一`source_ref`で2回生成したartifactが一致し、`created_at`が決定的sentinel (`1970-01-01T00:00:00Z`) であることを確認。
  - 候補レベル明示: `changed_files[].analysis_status = candidate_path_only_phase_0`、`confidence = 0.4`、`requires_human_review = true`。READMEにもPhase 0ではRequirement / Risk / APIへの意味的マッピングを行わないことを明記。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
