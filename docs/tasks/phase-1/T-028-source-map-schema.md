---
task_id: T-028
epic: grounding-oracle
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by:
---

# T-028: SourceMap schema定義

## 目的

W1(source grounding)の出力artifact `SourceMap`(§6.2)のJSON Schemaを定義する。Phase 0で未定義の残schemaのうちgrounding系を先に埋め、T-029(source-grounding skill)の出力契約を確定させる。

## 参照

- 計画: §5 epic分解(grounding-oracle)
- North Star: §6.1(基本ルール)、§6.2(SourceMap)

## DoD

- [ ] `schemas/source-map.schema.json` が作成され、ArtifactBase継承・§6.2のfield構成に従っている(Phase 0のschema群と同じ流儀)
- [ ] `uv run python scripts/gen_models.py` でPydanticモデルが再生成され、差分がコミットされている(`--check` がpass)
- [ ] artifact_validatorがSourceMapを検証できる(valid / invalid 各ケースのpytestで実証)
- [ ] `uv run pytest` / `uv run ruff check .` がpassする

## 検証方法・根拠

<完了時に記入: テスト結果、生成モデル差分検証の結果>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
