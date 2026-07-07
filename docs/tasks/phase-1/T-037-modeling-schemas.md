---
task_id: T-037
epic: modeling-generation
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by:
---

# T-037: StateModel / TestabilityReport schema定義

## 目的

W6(state modeling)とW8(testability analysis)の出力artifact `StateModel`(§6.5)と `TestabilityReport`(§6.8)のJSON Schemaを定義し、T-038 / T-039の出力契約を確定させる。

## 参照

- 計画: §5(modeling-generation)
- North Star: §6.1、§6.5、§6.8、§10(状態中心の検証)

## DoD

- [ ] `schemas/state-model.schema.json` と `schemas/testability-report.schema.json` が作成され、ArtifactBase継承・§6.5 / §6.8のfield構成に従っている
- [ ] `uv run python scripts/gen_models.py` で再生成したPydanticモデルがコミットされている(`--check` がpass)
- [ ] artifact_validatorが両schemaを検証できる(valid / invalid 各ケースのpytestで実証)
- [ ] `uv run pytest` / `uv run ruff check .` がpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
