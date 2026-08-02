---
task_id: T-026
epic: phase1-setup
plan_ref: phase-1-crud-mvp.md#7-リスクと未確定事項
status: done
owner:
blocked_by: [T-024]
---

# T-026: Source Connector最小版(OQ-4決定 + 対象repo PR diff取得)

## 目的

対象プロダクトrepoから変更差分(PR diff)と関連ドキュメントを取得するSource Connector最小版を実装する。W1(source grounding)の入力を供給する境界であり、対象固有の接続情報をここに隔離することで、skill本体をプロダクト非依存に保つ(計画§1の位置づけ)。

## 参照

- 計画: §1(固有知識の隔離方針)、§7(OQ-4)
- North Star: §5.1(Source Connectors)、§5.2(Ingestion & Normalization)

## DoD

- [x] OQ-4の決定(GitHub PR diff取得のみで開始するか、どのsource種別まで対応するか)が計画§7に記載され、`docs/plan/00-overview.md` の未決事項表でOQ-4が「決定済み(日付)」になっている
- [x] `source_connector/` で、対象repoのcommit rangeを指定してdiffと変更ファイル一覧を取得できる(CLI 1発。T-010の `parse_unified_diff` を再利用した)
- [x] 対象repo固有の設定(repo path、ラベル)がコードから分離された環境変数にあり、設定を差し替えれば別repoにも適用できる(テストで実証。下の読み替え参照)
- [x] 認証情報がコード・設定ファイルにハードコードされていない(下の読み替え参照)
- [x] `uv run pytest` で追加テストがpassし、`uv run ruff check .` がpassする
- [x] AGENTS.mdのリポジトリ構成マップに `source_connector/` の行が追加されている

## DoDからの読み替え(レビュー観点)

**「veridia自身を第2のrepoとして取得できることをテストで実証」** — T-024でveridia自身が**対象**になったため、veridiaは第1のrepoである。設定差し替えの実証には `vendor/sqk-core`(実在するローカルgit repo、オフラインで使える)を第2のrepoとして使った(`TestConfigurationIsSwappable::test_the_same_code_reads_a_second_repository`)。veridia自身が対象として読めることも別テストで固定している(`test_veridia_itself_is_readable_as_the_phase_1_target`)。

**「認証情報が環境変数参照。欠落時は文脈付きエラー」** — OQ-4の決定によりローカルgitのみを読むため、**veridiaは認証情報を一切扱わない**。したがって「環境変数から読む」対象が存在せず、この項目は空虚に成立する。空虚な成立を放置せず、代わりに**認証情報を扱わない設計そのもの**をテストで固定した(`TestNoCredentialsAreHandled`: モジュールのソースに `TOKEN` / `PASSWORD` / `SECRET` / `API_KEY` / `GH_TOKEN` が現れないことを検査)。repo pathの欠落時に文脈付きエラーを出すことは別途固定している。

## 検証方法・根拠

```bash
uv run pytest tests/test_source_connector.py -q     # 25 passed
VERIDIA_REQUIRE_SQK=1 uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run python -m source_connector --repo . --label veridia --base HEAD~1 --head HEAD --output /tmp/change.json
```

**mutation checkで防御テストの実効性を確認した**(全緑はDoDの必要条件でしかない。learning-log 2026-07-03)。意図的な欠陥8件を入れ、全件がテストで検出されることを確認:
`-` 始まりrevisionを拒否しない / 空revisionを許す / gitのexit codeを無視する /
解決できないrefを空SHAへ退化させる / 非gitディレクトリを受け入れる /
環境変数未設定を黙って既定値にする / 読めないdiff出力を「変更なし」にする / labelを無視して固定文字列でrefを作る

## 記録(完了時に記入)

- learning-log: [2026-08-02 共有parserの「入力エラー」は、呼び出し側では正当な結果でありうる](../../knowledge/learning-log.md)
- decisions: なし(OQ-4は計画§7へ記載。ADR不要)
- domain: なし(接続方法はveridia側の実装であり対象プロダクトの業務知識ではない)
