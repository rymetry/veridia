---
task_id: T-028
epic: grounding-oracle
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: done
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

- [x] `schemas/source-map.schema.json` が作成され、ArtifactBase継承・§6.2のfield構成に従っている(Phase 0のschema群と同じ流儀)
- [x] ~~`uv run python scripts/gen_models.py` でPydanticモデルが再生成され、差分がコミットされている~~ → **[ADR-0008](../../decisions/adr-0008-drop-generated-pydantic-models.md) で生成パイプライン自体を廃止済みのため実施しない**(T-054 DoDと同じ陳腐化)。artifact契約の検証は `artifact_validator` が schema を直読する
- [x] artifact_validatorがSourceMapを検証できる(valid / invalid 各ケースのpytestで実証。`tests/test_source_map_schema.py` 45件)
- [x] `uv run pytest` / `uv run ruff check .` がpassする

## 追加で必要になったこと(着手時に判明)

**1. ADR-0007の列挙との整合。** ADR-0007は「veridiaが自前で定義する契約は4つ」と列挙していた。`SourceMap` はsqk-coreに相当物が無く原則(実行系固有)には合致するが列挙とは食い違うため、[ADR-0009](../../decisions/adr-0009-contract-ownership-boundary.md) で**列挙ではなく原則で判定する**ことを決めてから実施した(変更ルール5)。オーナー合意済み(2026-08-02)。

**2. `trust_level` のauthorityの決定。** §6.2の `SourceMap` は `trust_level` を持つが、learning-log 2026-08-02「信頼ラベルをLLMに生成させるとtrust gateが自己申告で迂回できる」に該当する。**schemaは値域しか縛れず「誰が言ったか」を縛れない**ため、ADR-0009 Decision 2で値の決定主体をingestion層(`source_connector`)に固定し、実装も同時に入れた(コメントだけの約束にしない)。skill出力の上書き配線はT-029で行う。

## §6.2からの差分(レビュー観点)

| 差分 | 理由 |
|---|---|
| `version` → `source_version` へ改名 | §6.2の例は `version` にcommit shaを入れるが、ArtifactBaseの `version` はartifact自身のsemverで意味が衝突する |
| `extracted_items[].artifact_id` を必須にしない | W1時点では対応artifact(REQ-nnn等)がまだ存在しない(生成はW2)。必須にするとID捏造を強いる |
| 代わりに `span` を必須にする | 位置を言えない項目はgroundingになっていない |
| `extracted_items` は空配列を許す | 「このsourceからは何も取り出せなかった」は正当な結果 |

**ArtifactBaseは継承する。** producerはLLM skillであり `confidence` / `created_by.skill` / `model` を供給できる。非継承の例外(RunRecord / GateDecision)を増やさない側の実例。

## 検証方法・根拠

```bash
uv run pytest tests/test_source_map_schema.py tests/test_source_connector.py -q   # 75 passed
VERIDIA_REQUIRE_SQK=1 uv run pytest -q                                            # 947 passed
uv run ruff check . && uv run ruff format --check .
```

**mutation checkでtrust authorityの実効性を確認した。** 意図的な欠陥4件を入れ、全件がテストで検出されることを確認: 任意のtrustラベルを受け入れる / trust値域をschema導出でなくハードコードして乖離させる / ChangeSetが設定値を無視して固定値を返す / `__post_init__` の検証を外す。

## 記録(完了時に記入)

- decisions: [ADR-0009](../../decisions/adr-0009-contract-ownership-boundary.md)(契約の正本判定を列挙から原則へ / `trust_level` のauthorityをingestion層へ)
- learning-log: なし(ADR-0009に決定として記録した。実運用の学びが出たら追記する)
- domain: なし
