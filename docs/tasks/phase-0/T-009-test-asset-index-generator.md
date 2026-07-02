---
task_id: T-009
epic: artifact-schema
plan_ref: phase-0-foundation.md#2-完了条件
status: done
owner:
blocked_by: [T-006, T-008]
---

# T-009: TestAssetIndex generator最小版

## 目的

対象repoのテスト資産を走査してTestAssetIndexを生成する。計画§2完了条件「対象repoからTestAssetIndexを生成できる」をカバーし、schemaを実データで検証する。OQ-4(対象repo)未決の間はveridia自身をダミー対象とする(計画§6)。LLM不使用の決定的実装(計画§1のスコープ)。

## 参照

- 計画: §2 完了条件、§6 リスクと未確定事項(OQ-4)
- North Star: §6.13、§5.3(Test Asset Intelligence Layer)

## DoD

- [ ] コマンド1発で指定repoのテストファイルを走査し、TestAssetIndex JSONを生成できる(veridia自身を対象に実行して確認)
- [ ] 生成物に1件以上のテスト資産(path / type)が含まれ、T-008 validatorをpassする(テストで実証)
- [ ] Phase 0で取得できないfield(covered requirement / flake rate等)の扱い(null / 未収集の区別)が生成物とREADMEに明記されている

## 検証方法・根拠

- DoD 1: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python -m test_asset_index_generator . /tmp/veridia-test-asset-index.json`
  - 結果: `generated: /tmp/veridia-test-asset-index.json`
  - 出力要約: `artifact_type=test_asset_index`、`scope.repository=veridia`、`scope.branch=unknown`、`assets=11`。先頭asset例: `tests/test_artifact_base_schema.py` / `unit`
- DoD 2: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python -m artifact_validator /tmp/veridia-test-asset-index.json`
  - 結果: `valid: /tmp/veridia-test-asset-index.json`
  - pytest根拠: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_test_asset_index_generator.py` → 3 passed
    - `test_cli_generates_valid_test_asset_index_from_veridia_tests`: CLI 1発でveridia自身からJSONを生成し、`validate_artifact` passと1件以上のasset(path/type)を確認
    - `test_generator_is_deterministic_for_same_input`: 同一入力で2回生成したdictが完全一致することを確認
    - `test_phase_0_uncollected_fields_are_explicitly_marked`: Phase 0未収集fieldの表現を確認
- DoD 3: 生成物では `covered_requirements` / `covered_risks` / `oracle_refs` を空配列、`stability.flake_rate` / `last_failed_at` / `last_passed_at` を `null` とし、補助metadata `collection_status` に `uncollected_phase_0` を入れる。README: `test_asset_index_generator/README.md`

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
