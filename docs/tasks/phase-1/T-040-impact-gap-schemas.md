---
task_id: T-040
epic: quality-intelligence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by:
---

# T-040: TestImpactPlan / CoverageGap schema定義

## 目的

W11(test impact selection)とW10(gap analysis)の出力artifact `TestImpactPlan`(§6.10)と `CoverageGap`(§6.11)のJSON Schemaを定義し、T-042 / T-043の出力契約を確定させる。

## 参照

- 計画: §5(quality-intelligence)
- North Star: §6.1、§6.10、§6.11、§12(Quality Intelligence)

## DoD

- [ ] `schemas/test-impact-plan.schema.json` と `schemas/coverage-gap.schema.json` が作成され、ArtifactBase継承・§6.10 / §6.11のfield構成に従っている
- [ ] `uv run python scripts/gen_models.py` で再生成したPydanticモデルがコミットされている(`--check` がpass)
- [ ] artifact_validatorが両schemaを検証できる(valid / invalid 各ケースのpytestで実証)
- [ ] `uv run pytest` / `uv run ruff check .` がpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
