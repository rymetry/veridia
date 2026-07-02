# schemas/ — Artifact JSON Schema

North Star §6(成果物契約)のJSON Schema実装を置く。Phase 0 WS-A(`docs/plan/phase-0-foundation.md`)の成果物。

## ルール

- `artifact-base.schema.json` を共通契約(§6.1)として定義し、各artifact schemaは `allOf` で継承する
- 1 artifact type = 1ファイル。命名: `<artifact-type>.schema.json`(例: `requirement-spec.schema.json`)
- draft 2020-12 を使う(ADR-0002)。`$id` は `https://veridia.dev/schemas/<ファイル名>`(解決可能なURLではなく識別子)
- schemaはsemverでバージョン管理し、破壊的変更はADRを起票してから行う(§27.3)。schema自体のsemverは `$comment` に記す
- 変更したら `uv run python scripts/gen_models.py` でPydanticモデル(`models/`、生成物)を再生成してコミットする(CIがdiff検証する)
- Phase 0で定義する対象は計画md参照。§6の全27種を一括定義しない(just-in-time、§5.4.1)
