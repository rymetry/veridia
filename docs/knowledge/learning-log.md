# Learning Log

記法は [`README.md`](README.md) 参照。新しいエントリを上に追加する。

---

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
- アクション(変更したもの・リンク): `docs/plan/00-overview.md` のPhase 0 statusを `in_progress` へ修正(2026-07-02、オーナー承認済み)。AGENTS.md作業フロー本体は未改訂(改訂は将来判断)。

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
