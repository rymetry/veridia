---
task_id: T-002
epic: artifact-schema
plan_ref: phase-0-foundation.md#5-技術選定adr起票が必要な決定
status: not_started
owner:
blocked_by: [T-001]
---

# T-002: 開発環境scaffolding(build / test / lint)

## 目的

ADR-0002の決定に基づき、以降の全実装タスクが使うbuild / test / lint環境を整備する。AGENTS.mdの「実装規約」節(コード導入後に追記する、とされている箇所)を埋める。

## 参照

- 計画: §5 技術選定
- ADR-0002(T-001の成果物)

## DoD

- [ ] 依存インストール・テスト実行・lintがそれぞれ単一コマンドで実行でき、ローカルでの実行が成功する(実行ログで確認)
- [ ] サンプルテスト1件がパスする
- [ ] AGENTS.md「実装規約」にbuild / test / lintコマンドとスタックが追記されている
- [ ] `docs/tasks/phase-0/_index.md` をfrontmatterから再生成するスクリプトが追加され、その出力が現行の_index.mdと一致する(列仕様は `docs/tasks/README.md` 準拠。配置は実装時に決定)

## 検証方法・根拠

(完了時に記入。想定: 各コマンドの実行結果を貼付)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
