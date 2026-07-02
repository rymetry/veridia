# Learning Log

記法は [`README.md`](README.md) 参照。新しいエントリを上に追加する。

---

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
