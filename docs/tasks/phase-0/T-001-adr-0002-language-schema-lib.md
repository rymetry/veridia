---
task_id: T-001
epic: artifact-schema
plan_ref: phase-0-foundation.md#5-技術選定adr起票が必要な決定
status: done
owner:
blocked_by:
---

# T-001: ADR-0002 実装言語・schema lib決定

## 目的

OQ-1(実装言語・スタック)を確定する。計画§6の指示により、これがPhase 0の最初のタスク。未決のままWS-Aを始めると手戻りする。

## 参照

- 計画: §5 技術選定、§6 リスクと未確定事項(OQ-1)
- North Star: §22(技術スタック案)、§6.1(ArtifactBase継承の実装方式)

## DoD

- [x] `docs/decisions/adr-0002-language-schema-lib.md` が存在し、statusがaccepted(人間の承認を得る)
- [x] 実装言語、schema lib、JSON Schemaファイル(`schemas/`)とコード内schema定義の併用方針が決定されている
- [x] `docs/plan/00-overview.md` のOQ-1行が決定済み(ADRへのリンク付き)に更新されている

## 検証方法・根拠

- DoD 1: [ADR-0002](../../decisions/adr-0002-language-schema-lib.md) の存在と `- status: accepted` をファイル実体で確認。人間(オーナー)の承認は2026-07-02に実施され、承認時に確定した判断根拠(対象プロダクトの想定スタック、反転条件の評価)はADR末尾の追記に記録した
- DoD 2: 同ADRのDecision 1(実装言語: Python)/ Decision 2(schema lib: Pydantic v2 + `jsonschema` 併用)/ Decision 3(`schemas/` のJSON Schemaを正本、JSON Schema→Pydantic単方向生成、CI検証で乖離防止)が、DoDの3決定事項(言語・schema lib・併用方針)をすべてカバーしていることを確認
- DoD 3: `docs/plan/00-overview.md` 未決事項表のOQ-1行が「決定済み(2026-07-02)」+ ADR-0002へのリンク付きに更新されていることを確認

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: decisions → [ADR-0002](../../decisions/adr-0002-language-schema-lib.md)(実装言語・schema lib・schema正本方針)。domain / learning-log は該当なし
