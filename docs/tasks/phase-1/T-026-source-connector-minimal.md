---
task_id: T-026
epic: phase1-setup
plan_ref: phase-1-crud-mvp.md#7-リスクと未確定事項
status: not_started
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

- [ ] OQ-4の決定(GitHub PR diff取得のみで開始するか、どのsource種別まで対応するか)が計画§7に記載され、`docs/plan/00-overview.md` の未決事項表でOQ-4が「決定済み(日付)」になっている
- [ ] `source_connector/`(または相当モジュール)で、対象repoのPR(またはcommit range)を指定してdiffと変更ファイル一覧を取得できる(CLI 1発で実行して確認。Phase 0 T-010のdiff parserを再利用できる場合は再利用する)
- [ ] 対象repo固有の設定(repo URL、認証方法、ブランチ等)がコードから分離された設定ファイルまたは環境変数にあり、設定を差し替えれば別repoにも適用できる(veridia自身を第2のrepoとして取得できることをテストで実証)
- [ ] 認証情報がコード・設定ファイルにハードコードされていない(環境変数参照。欠落時は文脈付きエラー)
- [ ] `uv run pytest` で追加テストがpassし、`uv run ruff check .` がpassする
- [ ] AGENTS.mdのリポジトリ構成マップに新モジュール(`source_connector/` 等)の行が追加されている

## 検証方法・根拠

<完了時に記入: コマンドとその出力、テスト結果>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
