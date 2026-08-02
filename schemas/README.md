# schemas/ — Artifact JSON Schema

North Star §6(成果物契約)のJSON Schema実装を置く。Phase 0 WS-A(`docs/plan/phase-0-foundation.md`)の成果物。

## ルール

- `artifact-base.schema.json` を共通契約(§6.1)として定義し、各artifact schemaは `allOf` で継承する
  - **例外**: producerがArtifactBase必須fieldの真実を供給できないものは継承しない。値を埋めれば捏造になるため(learning-log 2026-08-02)。非継承schemaも `artifact_type` の `const` は持ち、artifact_validatorのルーティングには乗る
    - `run-record.schema.json`(ADR-0007の監査ラッパー) — artifactではなくartifactを運ぶ入れ物であり、`confidence` がrunに対して意味を持たない
    - `gate-decision.schema.json`(§6.24) — producerが決定的な評価器であり、`confidence` に加えて `created_by` の `skill` / `model` にも対応する値が無い
  - 上記2件は §6.1 の必須field(特に `confidence`)見直し提案に対するproducer証拠でもある。3件目が出たら見直しを起票する
- **handoff-envelope に載せるときの `schema_ref` は `veridia://schemas/<ファイル名>`**([ADR-0010](../docs/decisions/adr-0010-handoff-envelope-for-both-contract-families.md))。素の `schemas/<ファイル名>` は sqk-core 契約の名前空間であり、veridia 契約には使わない。family間のフォールバックは無いため、名前空間を間違えた ref は黙って通らず解決に失敗する
- **どの契約をveridiaが定義するかは列挙ではなく原則で判定する**([ADR-0009](../docs/decisions/adr-0009-contract-ownership-boundary.md))。sqk-coreが正本を持つのはテストプロセス成果物(11工程モデルの工程0〜8)。veridiaが正本を持つのは実行の記録・監査 / 判定と統制 / 取り込み境界のいずれかで、かつsqk-coreに相当物が無いもの。ADR-0007の4件の列挙は採択時点の適用結果であり閉じた集合ではない
- 新しいschemaを継承なしで足す場合は、どの必須fieldをproducerが供給できないのかをschemaの `description` に書き、契約テストで非継承を固定する(`tests/test_run_record_schema.py::TestSchemaItself::test_does_not_inherit_artifact_base` が参照実装)
- `$ref` は相対ファイル名(例: `"artifact-base.schema.json"`)で書く。`$id` は解決可能なURLではないため、検証する側は全schemaを `$id` で引ける `referencing.Registry` を組んでvalidatorへ渡すこと(registryなしの単体 `Draft202012Validator(schema)` は `Unresolvable` で失敗する)。参照実装: `tests/test_core_spec_schemas.py` の `build_registry()`
- 開いたobject(追加fieldを許す)は `"additionalProperties": true` を省略せず明示する。省略すると生成Pydanticモデルが `extra=ignore` になり追加fieldを黙って捨てる(learning-log 2026-07-02参照)。**例外**: 合成用のbase schema(`artifact-base.schema.json`)には宣言しない — base側で `additionalProperties: true` を宣言すると全propertyが「評価済み」になり、子schemaの `unevaluatedProperties: false` による閉鎖が無効化されるため
- 1 artifact type = 1ファイル。命名: `<artifact-type>.schema.json`(例: `requirement-spec.schema.json`)
- draft 2020-12 を使う(ADR-0002)。`$id` は `https://veridia.dev/schemas/<ファイル名>`(解決可能なURLではなく識別子)
- schemaはsemverでバージョン管理し、破壊的変更はADRを起票してから行う(§27.3)。schema自体のsemverは `$comment` に記す
- Pydanticモデルの生成は行わない(ADR-0008で廃止)。schemaを変更したら `uv run pytest` で契約テストを確認する
- Phase 0で定義する対象は計画md参照。§6の全27種を一括定義しない(just-in-time、§5.4.1)
