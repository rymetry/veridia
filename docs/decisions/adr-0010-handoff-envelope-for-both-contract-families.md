# ADR-0010: handoff-envelope を両contract familyの受け口にする

- status: accepted
- date: 2026-08-02

## Context(何を決める必要があったか)

T-029(`source-grounding` skill)は **veridia自前のskill**(`qa-skills/`)を初めて作るタスクである。その出力は [ADR-0009](adr-0009-contract-ownership-boundary.md) で veridia が正本を持つと決めた `SourceMap` であり、sqk-core の契約ではない。

一方、現在の skill 実行・監査経路は sqk-core 専用に作られていた。

| 箇所 | 現状 |
|---|---|
| `artifact_validator.sqk_schema_store.resolve_schema_path` | `vendor/sqk-core/schemas/` 外の `schema_ref` を明示的に拒否する |
| `schemas/run-record.schema.json` の `sqk_core.commit` | 必須。veridia自前skillの実行には対応する値が存在しない |
| `skill_runner.contract_note` | sqk-core schemaしか読まない |

このままだと、veridia自前skillの出力は `RunRecord` に載らず、`GateDecision` の評価対象にもならない。**監査経路が2系統に分かれる。**

さらに名前空間の衝突がある。sqk-core の `schema_ref` は `schemas/<file>.schema.json` 形式で、veridia の schema も `schemas/` に置かれているため、素の相対パスでは**どちらの family か判別できない**。

## Decision(何を決めたか)

### 1. veridia自前skillも handoff-envelope を出す。envelope は両familyの受け口になる

`RunRecord` / `GateDecision` / store / gate評価は変更せずそのまま使える。監査経路は1本のまま。ADR-0007 が定めた「2つのschema familyを別ルーティングで扱う」の自然な延長であり、mapping層やadapter層は引き続き作らない。

### 2. `schema_ref` の名前空間を明示する。暗黙のフォールバックはしない

```text
schemas/<file>.schema.json           … sqk-core契約(上流の慣習。veridiaが変えない)
veridia://schemas/<file>.schema.json … veridia契約
```

解決できない `schema_ref` はエラーにする。**「sqk-coreで引けなければveridiaを試す」というフォールバックは実装しない** — 同名schemaが両familyに現れた瞬間に、どちらを検証したのか分からないまま通る経路ができる。今は衝突が無いが、無いことに依存した設計にしない。

### 3. `RunRecord.sqk_core` は条件付き必須にする(schema 0.3.0)

envelope が sqk-core の `schema_ref` を1つでも宣言していれば必須、していなければ**禁止**する。

- 「必須ではない」で済ませると、veridia自前runに無意味なSHAが入った record を後から区別できない
- 強制は producer(`run_store.build_run_record`)で行う。JSON Schema からは envelope 内の `schema_ref` を見て条件分岐する記述が書けるが、壊れやすく読めない

veridia自前契約の版はどこに残るのか: artifact 自身が ArtifactBase の `version`(semver)を持つ。sqk-core 契約が SHA 固定を更新手段にしている(ADR-0006)のに対し、veridia 契約は schema 自身が semver を持つため、記録すべき場所が違うだけで欠落はしない。

### 4. `contract_note` は `$ref` / `allOf` を解決してから制約を集める

veridia schema は ArtifactBase を `allOf` で継承する。継承先の制約(`version` の semver `pattern` 等)を辿らないと、**モデルは自分が何で検証されるかを知らないまま出力する** — learning-log 2026-08-02 で実測した失敗モードそのものが veridia 契約側で再発する。

### 却下した代替案

| 代替案 | 却下理由 |
|---|---|
| 自前skillはenvelopeを使わず`SourceMap`を直接出す | 監査記録が2系統に分かれる。gate評価器は `RunRecord` を見ているため、自前skillの出力がgateの対象外になる。後から合流させるコストの方が高い |
| `schema_ref` は素の相対パスのままにし、sqk-core → veridia の順で解決する | 同名schemaが現れた瞬間に、どちらを検証したのか分からないまま通る。名前空間の衝突は「今は無い」だけで、構造的に防げていない |
| `sqk_core` を単に optional にする | 「無くてよい」だけでは、veridia自前runに無関係なSHAが入った record を弾けない。**条件付き必須**にして初めて、record を見ればどちらのfamilyの実行か判別できる |
| sqk-core に `source-grounding` skill を起票する | grounding は veridia の ingestion 固有の関心で、sqk-core の11工程モデルの外側にある(ADR-0009 で同じ理由により却下した案と同型) |

## Consequences(トレードオフ、影響)

- **利点(監査経路が1本)**: どちらのfamilyのskillでも `RunRecord` → `GateDecision` が同じ経路で通る。gate評価器は変更不要
- **利点(判別可能性)**: `sqk_core` の有無で、その run がどちらのfamilyの契約を満たすものか record 単体から分かる
- **コスト(schema変更)**: `run-record.schema.json` を 0.2.0 → 0.3.0 へ。既存recordは `sqk_core` を持つため後方互換だが、`required` から外れることで「必ずある」と仮定した読み手は壊れうる
- **コスト(ref表記の非対称)**: sqk-core 側は `schemas/...`、veridia 側は `veridia://schemas/...` と形が揃わない。上流の慣習を変えないための代償であり、揃えるなら sqk-core 側の変更が要る(1 consumer の都合を正典へ持ち込まない、ADR-0007)
- **North Star への影響**: なし(§6 の契約定義そのものは変えていない)
