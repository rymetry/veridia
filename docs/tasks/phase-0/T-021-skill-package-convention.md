---
task_id: T-021
epic: skill-registry-gatepolicy
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-002]
---

# T-021: skill package規約とtemplate skeleton

## 目的

Phase 1でskill群を実装するための規約を確定する。§7.1のpackage構造に従うtemplateを `qa-skills/` に置き、manifest必須項目(§7.2)を機械検証可能にする。

## 参照

- 計画: §3 WS-E
- North Star: §7.1(Skillの構造)、§7.2(manifest例)
- `qa-skills/README.md`(ADR-0001の名前空間注意を含む)

## DoD

- [x] `qa-skills/_template/` に§7.1のpackage構造に対応するskeletonが存在する(構成要素の網羅は§7.1のディレクトリ図との突き合わせで確認。各ファイルは構造を示すstubで可)
- [x] manifestの必須項目セットを§7.2の例から定義してschema化し(§7.2は例示のため、どのkeyを必須とするかはschema側で確定させる)、templateのmanifestがvalidationをpassする(テストで実証)
- [x] `qa-skills/README.md` にtemplateの使い方(新規skill作成手順)が追記されている

## 検証方法・根拠

- DoD 1 (`qa-skills/_template/` skeleton): `tests/test_skill_manifest_schema.py::TestTemplatePackage::test_template_contains_section_7_1_package_structure` で§7.1の構成要素(`SKILL.md`, `manifest.yaml`, `input.schema.json`, `output.schema.json`, `preconditions.md`, `postconditions.md`, `failure_modes.md`, `examples/`, `evals/`, `validators/`, `scripts/`, `changelog.md`)の存在を検証。`UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_skill_manifest_schema.py -q` → `34 passed`。
- DoD 2 (manifest必須項目schema化 + template validation): `qa-skills/manifest.schema.json` を追加。skill manifestはartifactではなくPydanticモデル生成不要のため `schemas/*.schema.json` ではなく `qa-skills/` 配下に置いた(この判断はschema `$comment` / `description` と `qa-skills/README.md` に記録)。必須項目は、Phase 0-1のskill authorが必ず書け、T-022 registry metadataが依存する `name` / `version` / `owner` / `description` / `inputs` / `outputs` に限定。`trigger` / `preconditions` / `quality_gates` / `validators` / `failure_modes` は存在する場合に検証するoptional field。`tests/test_skill_manifest_schema.py` でtemplate manifestのpass、必須項目欠落、型・値違反を検証。`UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_skill_manifest_schema.py -q` → `34 passed`。
- DoD 3 (`qa-skills/README.md`): 新規skill作成手順、manifest schema正本、必須項目セット、T-022 registry metadataとの対応を追記。
- 全体検証: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest` → `493 passed`。
- Lint/format: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff check .` → `All checks passed!`; `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff format --check .` → `83 files already formatted`。
- 生成モデル整合: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python scripts/gen_models.py --check` → `ok: /Users/rym/Dev/personal-projects/veridia/models は /Users/rym/Dev/personal-projects/veridia/schemas の再生成結果と一致`。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし(必須項目セットとschema配置判断は `qa-skills/manifest.schema.json` と `qa-skills/README.md` に記録)
