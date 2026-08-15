# Agent Context

<!-- プロジェクト概要をここに記載してください。 -->

## コマンド

<!-- プロジェクトで使うコマンドを記載してください。例:
- Build: `...`
- Test: `...`
- Lint: `...`
-->

## ルール

- Secrets やローカル環境固有の状態をコミットしない。
- `main` へ直接 push しない。変更は PR 経由で反映する。
- `main` への force push は禁止(`.claude/hooks/pre-tool-use-policy.sh` でブロックされる)。
- コンフリクトマーカーを残したまま作業を終えない(`.claude/hooks/stop-verify.sh` で検出される)。
