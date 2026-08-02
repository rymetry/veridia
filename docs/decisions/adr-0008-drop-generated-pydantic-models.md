# ADR-0008: 生成Pydanticモデル(`models/`)と生成パイプラインを廃止する

- status: accepted
- date: 2026-08-02
- supersedes: [ADR-0002](adr-0002-language-schema-lib.md) Decision 3 のうち「JSON Schema → Pydanticモデル単方向生成 + CI diff検証」の部分(正本方針=`schemas/*.schema.json` が正本、は維持)

## Context(何を決める必要があったか)

ADR-0002 Decision 3 は `datamodel-code-generator` による schema → Pydantic 単方向生成と、生成物のコミット + CI diff 検証を定めた。目的は「JSON Schema とコードの二重管理による乖離の防止」である。

運用実績を測ったところ、次が確認できた。

- **`models/` を import している非テストコードが1つも存在しない。** `artifact_validator` / `evidence_store` / `trace_store` / `tool_gateway` / `sandbox_*` / 各generator / CLI のいずれも `schemas/*.schema.json` を直接読む。唯一の利用者は「生成が正しく行われたことを検証するテスト」であり、自己参照的である
- これは事故ではなく設計どおりである。ADR-0002 自身が Consequences で「T-008のvalidatorは必ず `schemas/*.schema.json` を参照する実装にする」と定めており、gate入力になる契約検証の経路に Pydantic は最初から入っていない(T-008の判断は learning-log 2026-07-03 に記録)
- **防ぐべき「二重管理」が実在しない。** 管理されているのは JSON Schema のみで、Pydantic 側は誰も読まない生成物である
- コスト側: learning-log 13エントリのうち**6エントリが本パイプラインの罠**(array item制約のRootModel具象化、`additionalProperties` 省略時の silent data loss、子schema再宣言時のOptional化、`uniqueItems` 非強制、modular refs のディレクトリ出力強制、生成timestampの非決定性)。実体は `models/` 915行 + `scripts/gen_models.py` 248行 + `tests/test_gen_models.py` 283行 + CI 1ステップ + dev依存1件
- ADR-0002 Decision 3 の根拠は「§6.1が全27 artifactの `allOf` 継承を前提としており、契約の一覧性を保つには宣言的なJSON Schemaを正本に据えるのが乖離に強い」だった。[ADR-0007](adr-0007-sqk-core-contract-consumption.md) により **veridiaが定義する契約は27→4になり、この前提自体が消滅した**

ADR-0002 は「見直し条件」として `allOf` 継承の生成が破綻した場合を挙げ、その際は「正本方針=Decision 3のみのsupersedeで足りる可能性がある」と予期していた。破綻ではなく前提消滅という別経路だが、supersede範囲は同じである。

## Decision(何を決めたか)

**`models/` と生成パイプラインを削除する。`schemas/*.schema.json` が正本である点(ADR-0002 Decision 3 の前半)は維持する。**

削除対象:

| 対象 | 行数 |
|---|---|
| `models/`(生成物) | 915 |
| `scripts/gen_models.py` | 248 |
| `tests/test_gen_models.py` | 283 |
| 他テストの `TestGeneratedModels` クラスおよび生成モデル非対称性の pin テスト4件 | 約90 |
| `.github/workflows/ci.yml` の「生成Pydanticモデル差分検証」ステップ | 2 |
| `pyproject.toml` の dev依存 `datamodel-code-generator` と ruff `extend-exclude` の `models` | - |

削除するテストはすべて生JSON側に対応するテストを持つ(`test_schema_embedded_examples_pass` / `test_missing_domain_required_field_fails` / `test_signal_extra_fields_pass` / `test_log_entry_preserves_extra_fields` / `test_duplicate_oracle_type_fails`)。**契約カバレッジは減らない。**消えるのは「JSON Schema と生成モデルの強制範囲の非対称性」を固定するテストであり、生成モデルが無くなれば非対称性自体が存在しない。

### 却下した代替案

| 代替案 | 却下理由 |
|---|---|
| 生成を残し、runtimeコードから使うようにする | 使う理由が無い。契約検証の正本は生JSON(ADR-0002 の明示的な設計)であり、Pydantic経由にすると生成漏れ時の乖離を見逃すと ADR-0002 自身が警告している |
| 生成物をコミットせずビルド時生成のみにする | 誰も使わないものを毎ビルド生成することになる。ADR-0002 が「個人開発では追跡する方が差分レビューしやすい」として選んだ方式の利点だけを捨て、コストは残る |
| `models/` は残しCI検証だけ外す | 検証のない生成物はschemaと静かに乖離する。使われない上に信用できない成果物が残るのが最悪 |

## Consequences(トレードオフ、影響)

- **利点**: 約1,540行と依存1件が消える。learning-log の6罠に対する保守が不要になる。schema追加時の手順が「JSONファイルを1つ足す」だけになる(再生成・diff確認が不要)
- **失うもの**: artifact を型付きで扱いたくなったときの既製手段。必要になった時点で (a) 対象を絞って手書き frozen dataclass を置く、(b) 生成を再度有効化する、のどちらかを選ぶ。**`schemas/` が正本のままなので (b) は `datamodel-code-generator` の再導入だけで戻せる**(本ADRのsupersedeを解除するADRを起票すること)
- **CI**: 検証ステップが1つ減る。残る検証(lint / format / pytest / `_index` 差分)は不変
- **ADR-0002 との関係**: Decision 1(Python)・Decision 2(Pydantic v2 + jsonschema の採用自体)・Decision 3 前半(JSON Schema が正本)は有効。Pydantic は依存として残る(将来の型付き表現・他用途のため)が、artifact契約の生成には使わない
- **見直し条件**: veridia が artifact を型付きで扱うruntimeコードを持ち、手書き dataclass では管理しきれない規模(目安: 対象artifact 5種以上)になった場合、本ADRをsupersedeして生成を再導入する
