# Agent Context

Veridia — 開発の各フェーズに品質の観点を持ち込む、対話型Skill+テンプレートのハーネス。
`skills/` と `templates/` が正本。設計思想は `docs/operating-model.md` を参照。

## コマンド

- 構造検証: `bash scripts/validate.sh`(Skill規約・パス参照・installer の動作)
- 対象プロジェクトへの導入: `./install.sh <対象プロジェクトのパス>`

## ルール

- Secrets やローカル環境固有の状態をコミットしない。
- `main` へ直接 push しない。変更は PR 経由で反映する。
- `main` への force push は禁止(`.claude/hooks/pre-tool-use-policy.sh` でブロックされる)。
- コンフリクトマーカーを残したまま作業を終えない(`.claude/hooks/stop-verify.sh` で検出される)。
