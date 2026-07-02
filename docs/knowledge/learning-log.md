# Learning Log

記法は [`README.md`](README.md) 参照。新しいエントリを上に追加する。

---

## 2026-07-02 [process-learning] allOf外部$ref(modular reference)はdcgのファイル単位生成と両立しない — ディレクトリ一括生成へ移行(T-004)

- 事実(何を観測したか): T-004でspec schemaが `allOf: [{"$ref": "artifact-base.schema.json"}]` を持った時点で、datamodel-code-generator(0.66.3)のファイル単位 `--output <file>.py` が「Modular references require an output directory」で失敗。ディレクトリ入力+ディレクトリ出力の一括生成に切り替えると成功し、`class RequirementSpec(ArtifactBase)` というクラス継承+モジュール間importが生成される。付随の実測: (1) モジュール名はdcg規則で `<type>_schema.py` になる(旧 `<type>.py` から改名)。(2) `__init__.py` も生成物になる(models/ は名前空間パッケージから通常パッケージへ)。(3) dcg既定ヘッダは入力ディレクトリ名(=一時dir名)を `__init__.py` に埋めて決定性を壊すため `--custom-file-header` で置換が必要。(4) 一括実行はschema parse失敗時のエラーにファイル名を含めないため、事前に個別JSON parseで文脈を付与する必要がある。(5) 入力ディレクトリに非schemaファイル(README等)があるとYAMLとしてparseして失敗するため、一時ディレクトリへ `*.schema.json` のみコピーして渡す。
- 学び(なぜ・何を変えるべきか): 生成器の制約がモジュール命名などリポジトリ規約側に波及する。schema間参照(継承)を導入する時は、生成側の挙動(命名・決定性・エラー文脈)を先に実測してから規約を確定する。
- アクション(変更したもの・リンク): `scripts/gen_models.py` をディレクトリ一括生成へ書き換え([T-004](../tasks/phase-0/T-004-core-spec-schemas.md))。生成物は `models/artifact_base_schema.py` 等へ改名(T-003記録に追記済み)。regression guard: `tests/test_gen_models.py`(継承の生成・`__init__.py` ヘッダ・決定性・orphan掃除)。

## 2026-07-02 [process-learning] uniqueItems等、dcgがPydantic制約へ変換しないJSON Schema制約がある(生JSONのみ強制の非対称)

- 事実(何を観測したか): `oracle_type` の `uniqueItems: true` は生JSON検証では重複をrejectするが、dcg(0.66.3)生成モデルは `list` のまま重複を通す(T-004の2次レビューで検出、実測再現済み)。`format: date-time`(T-003)とは逆向きの非対称(あちらは生JSONが緩く生成モデルが厳しい)。
- 学び(なぜ・何を変えるべきか): JSON Schema制約と生成モデルの強制範囲は一致しない前提で扱う。非対称を見つけたら「schema description/$commentへの明記+挙動を固定するregression test」をセットで置く(Signal extra / naive datetimeと同じ扱い)。gateの入力になる契約検証は生JSON側(T-008 validator)を正とする。
- アクション(変更したもの・リンク): `schemas/oracle-spec.schema.json` のdescriptionへ明記。`tests/test_core_spec_schemas.py::test_generated_model_does_not_enforce_unique_oracle_type` で挙動を固定。

## 2026-07-02 [process-learning] 開いたobjectは additionalProperties: true を明示しないと生成モデルが追加fieldを黙って捨てる(T-005〜T-007への注意)

- 事実(何を観測したか): OracleSpec.signals のitem(type毎に異なるfieldを持つ開いたobject)で `additionalProperties` を省略(=JSON Schema既定のtrue)したところ、dcg生成の `Signal` モデルはPydantic既定の `extra=ignore` になり、`model_dump()` のround-tripで `query_ref` / `endpoint` 等の中身が黙って消えた(silent data loss)。schema側に `"additionalProperties": true` を明示すると `extra='allow'` が生成され保持される。
- 学び(なぜ・何を変えるべきか): JSON Schemaの既定値と生成コードの既定値は一致しない。「開いておく」意図は省略ではなく明示で表現する。開いたobjectには生成モデルのround-trip保持テストを置く。
- アクション(変更したもの・リンク): `schemas/oracle-spec.schema.json` のsignals itemに `additionalProperties: true` を明示($commentに理由)。regression guard: `tests/test_core_spec_schemas.py::test_generated_signal_model_preserves_extra_fields`。

## 2026-07-02 [process-learning] 子schemaでconst再宣言したfieldは子のrequiredにも再列挙しないと生成モデルがOptional化する(T-005〜T-007への注意)

- 事実(何を観測したか): `artifact_type` をbase側required+子側 `const` 再宣言のみとした場合、dcg生成の子クラスは `artifact_type: Literal['requirement_spec'] | None = None` になり、base側の必須が子のfield再定義で上書きされて緩む(生JSON検証はallOf合成で必須のまま=生成モデルとの非対称)。子の `required` に `artifact_type` を再列挙すると必須の `Literal[...]` になる。
- 学び(なぜ・何を変えるべきか): Pydanticの継承はfield再定義が完全上書きのため、「子schemaで再宣言したfieldは子のrequiredにも再列挙する」を規約にする。T-005〜T-007のspec schema定義でも同じ確認を行うこと。
- アクション(変更したもの・リンク): コアspec 3 schemaの `required` へ `artifact_type` を追加。`tests/test_core_spec_schemas.py::test_required_matches_domain_required` が「domain必須 ∪ {artifact_type}」との完全一致を検証する。理由はschema descriptionにも記載。

## 2026-07-02 [process-learning] package=false構成では生成モデル(models/)のimportがpytest経由でしか解決されない(T-008への申し送り)

- 事実(何を観測したか): T-003の徹底レビューで、`uv run python scripts/<script>.py` のような通常のスクリプト実行では `models/` がimportできないことを実測確認(`sys.path[0]` はスクリプト自身のディレクトリでありcwdではない)。pytest下ではpyproject.tomlの `pythonpath = ["scripts", "."]` で解決される。`[tool.uv] package = false` のためプロジェクト自体はinstallされない。
- 学び(なぜ・何を変えるべきか): 生成モデルをテスト以外のランタイムコード(validator lib/CLI等)から使う段になったら、import解決方式(srcレイアウト化+`package = false` 見直し / パッケージ化 / sys.path運用)を決める必要がある。scaffolding時点の `package = false` は「コードがscripts/しか無い」前提の判断で、コードベースが育つと見直し対象になる。
- アクション(変更したもの・リンク): pytest側は `pythonpath` に `"."` を明示して`__init__.py`・import-mode非依存にした(T-003)。ランタイム側の方式決定は[T-008](../tasks/phase-0/T-008-artifact-validator.md)へ申し送り(タスク参照節に追記済み。ADR-0002委任範囲を超える場合はADRを起票する)。

## 2026-07-02 [process-learning] JSON Schemaのarray itemに制約を付けると生成Pydanticモデルが名前付きRootModelに具象化される(T-004〜T-007への注意)

- 事実(何を観測したか): T-003で `source_refs` のitemsに `minLength: 1` を付けたところ、datamodel-code-generator(0.66.3)が `list[str]` ではなく `SourceRef(RootModel[str])` のlistを生成した。要素の等価比較・`in`判定・`startswith` 等が静かに壊れる(code reviewでHIGH指摘)。`--collapse-root-models` / `--use-annotated` でも解消しない。
- 学び(なぜ・何を変えるべきか): 「schema→コード単方向生成」方式では、schema上の表現の選び方が生成コードのAPI品質を左右する。array itemへのスカラー制約は具象化トリガーになるため、契約上必須でない限り避ける。North Star/ADRが要求しない自前の追加ハードニングは、生成物への影響を確認してから入れる。生成モデルには値セマンティクスのregressionテスト(例: 要素が素のstrであること)を置く。
- アクション(変更したもの・リンク): `schemas/artifact-base.schema.json` のitem側minLengthを除去(`minItems: 1` は維持=ADR-0002の要求)。`tests/test_gen_models.py::test_source_refs_items_are_plain_strings` をregression guardとして追加。schema内 `$comment`/descriptionに理由を記載。T-004〜T-007のschema定義でも同じ確認を行うこと。

## 2026-07-02 [process-learning] 決定的diff検証には出力に埋まる「生成時刻」類を入力で固定できる設計が要る(CI初配線の学び)

- 事実(何を観測したか): T-003でCI(GitHub Actions)を初配線した際、`regen_task_index --check` は `--generated-on` の既定が実行日のため、内容が最新でもコミット済み `_index.md` と日付だけで不一致(exit 1)になることを確認した。datamodel-code-generatorも既定ではtimestampをheaderに埋め、formatterの既定も将来変わる予告(FutureWarning)があり、いずれも「再生成→diff無し」検証を壊す要因になる。
- 学び(なぜ・何を変えるべきか): 「生成物をコミットしCIで再生成→diff無しを検証する」方式(ADR-0002)は、生成が決定的であることが前提。実行時刻・ツール既定値など入力以外に依存する要素は、生成コマンド側で固定(disable / 明示指定)するか、コミット済みの値を入力として渡す。
- アクション(変更したもの・リンク): `scripts/gen_models.py` は `--disable-timestamp` とformatter明示(black / isort)で最初から決定化。`.github/workflows/ci.yml` の_index検証はコミット済み `_index.md` から生成日を抽出して `--generated-on` へ渡す方式にした。

## 2026-07-02 [process-learning] PhaseレベルstatusのUpdate手順が作業フローに無く、T-001完了時に更新漏れ

- 事実(何を観測したか): T-001がdoneになった時点でPhase 0は着手済みだったが、`docs/plan/00-overview.md` のPhaseレベルstatusは `not_started` のまま残っていた(T-002の監督レビューで検出)。AGENTS.md作業フロー(タスク実行時)には `_index.md` の再生成(手順5)はあるが、「Phaseの最初のタスクがdoneになったら00-overviewのPhaseレベルstatusを更新する」手順が明記されていない。
- 学び(なぜ・何を変えるべきか): statusの持ち場が2層ある(タスクレベル=各タスクfrontmatter、Phaseレベル=00-overview。変更ルール3)のに、作業フローがタスクレベルの更新しか規定していないため、Phaseレベルの更新はトリガーを失い漏れる。Phase statusが変わる契機(最初のタスクdone、Phase完了判定)を作業フローに組み込むかは将来判断(フロー改訂はこのエントリのスコープ外)。
- アクション(変更したもの・リンク): `docs/plan/00-overview.md` のPhase 0 statusを `in_progress` へ修正(2026-07-02、オーナー承認済み)。AGENTS.md作業フロー本体は未改訂(改訂は将来判断)。(2026-07-02追記: `phase-0-foundation.md` 冒頭に残っていたstatus複製行(`not_started` のまま)をT-004徹底レビューで検出し、status値を複製しない参照のみの行へ修正して二重管理を解消。)

## 2026-07-02 [process-learning] datamodel-code-generator生成コマンド+CI diff検証をT-003へ申し送り

- 事実(何を観測したか): ADR-0002 Consequences「後続タスクへの影響」でT-002に「datamodel-code-generatorの生成コマンドとCI diff検証を整備する」と書かれているが、T-002時点では `schemas/*.schema.json`(生成の入力=正本)がまだ1つも存在しない(実体はT-003以降で作られる)。入力の無い生成コマンドを配線しても検証できず、意味のあるCI diffチェックにならない。
- 学び(なぜ・何を変えるべきか): 生成コマンド+CI diff検証は「schema実体があること」に依存するため、T-002(scaffolding)ではなくschema定義タスク側で整備するのが正しい依存順序。T-002ではdatamodel-code-generatorをdev依存として用意するに留め、生成の配線はT-003に持たせる。
- アクション(変更したもの・リンク): datamodel-code-generatorを `pyproject.toml` の dev グループに追加(ツールは先行して利用可能)。生成コマンド(`datamodel-code-generator --input-file-type jsonschema` 相当)とCI再生成→diff無し検証の配線はT-003([T-003](../tasks/phase-0/T-003-artifact-base-schema.md))のDoDで実施する申し送りとする。これはADR-0002が具体化をT-002へ委任した範囲内の判断であり新規ADRは不要。

<!-- テンプレート
## YYYY-MM-DD [型] タイトル

- 事実(何を観測したか):
- 学び(なぜ・何を変えるべきか):
- アクション(変更したもの・リンク):
-->
