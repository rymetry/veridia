---
task_id: T-022
epic: skill-registry-gatepolicy
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-021]
---

# T-022: skill registry metadata定義

## 目的

skillの運用metadata(§28.2「残すもの」)を保持するregistry形式を定義する。独立Agent Registryは作らない(§28.2の判断)ため、リポジトリ内のindexファイルとして最小実装する。

## 参照

- 計画: §3 WS-E
- North Star: §28.2「残すもの」(registry metadata項目一覧の正本。ここに複製しない)

## DoD

- [x] registry index(例: `qa-skills/registry.yaml`)の形式が定義され、§28.2「残すもの」の全項目を保持できる(schemaで検証)
- [x] template skill(T-021)のentryが登録され、validationをpassする(テストで実証)
- [x] registry entryとskillディレクトリの整合(存在チェック、version一致)を検証するチェックがある

## 検証方法・根拠

- registry index形式: `qa-skills/registry.schema.json` と `qa-skills/registry.yaml` を追加。`tests/test_skill_registry.py::TestSkillRegistrySchemaItself::test_section_28_2_fields_are_represented_by_entry_properties` でNorth Star §28.2「残すもの」の全metadata fieldがentry schema propertiesとして表現されていることを検証。
- template skill entry: `qa-skills/registry.yaml` に `skill_id: template-skill` / `version: "0.1.0"` / `owner: qa-platform` / `package_path: _template` のentryを追加。`tests/test_skill_registry.py::TestSkillRegistry::test_registry_yaml_passes_schema` と `tests/test_skill_registry.py::TestSkillRegistry::test_template_skill_entry_is_registered` で検証。
- 不正entry validation: `tests/test_skill_registry.py::TestSkillRegistry::test_missing_required_entry_field_fails` と `tests/test_skill_registry.py::TestSkillRegistry::test_type_or_value_violation_fails` で必須欠落・型/値違反がfailすることを検証。
- registry entryとskill directoryの整合: `scripts/skill_registry.py::validate_registry_consistency` を追加し、`tests/test_skill_registry.py::TestSkillRegistryConsistency::test_registry_entries_match_existing_skill_directories_and_manifest_versions` / `test_missing_skill_directory_is_detected` / `test_manifest_version_mismatch_is_detected` で存在チェックとversion一致チェックを検証。
- 実行結果: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_skill_registry.py -q` → `35 passed in 0.13s`。
- 完了前の全体検証:
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest` → `528 passed`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff check .` → `All checks passed!`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff format --check .` → `85 files already formatted`

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし(§28.2からの逸脱なし。Phase 0未収集値は既存learning-log 2026-07-02の必須度原則に沿ってschemaで `null` / `not_collected` を許可)
