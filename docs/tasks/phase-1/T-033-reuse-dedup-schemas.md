---
task_id: T-033
epic: test-asset-reuse
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by:
---

# T-033: TestReuseCandidate / DuplicateTestReport schema定義

## 目的

W5(reuse / dedup analysis)の出力artifact `TestReuseCandidate`(§6.14)と `DuplicateTestReport`(§6.15)のJSON Schemaを定義し、T-035 / T-036の出力契約を確定させる。

## 参照

- 計画: §5(test-asset-reuse)
- North Star: §6.1、§6.14、§6.15、§13(Test Asset Reuse)

## DoD

- [ ] `schemas/test-reuse-candidate.schema.json` と `schemas/duplicate-test-report.schema.json` が作成され、ArtifactBase継承・§6.14 / §6.15のfield構成に従っている
- [ ] `uv run python scripts/gen_models.py` で再生成したPydanticモデルがコミットされている(`--check` がpass)
- [ ] artifact_validatorが両schemaを検証できる(valid / invalid 各ケースのpytestで実証)
- [ ] `uv run pytest` / `uv run ruff check .` がpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
