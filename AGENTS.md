# Agent Context

Veridia — 開発の各フェーズに品質の観点を持ち込む、対話型Skill+テンプレートのハーネス。
`skills/` と `templates/` が正本。設計思想は `docs/operating-model.md` を参照。

## セットアップ(clone後に1回)

```bash
git config core.hooksPath .githooks
```

git hooks(main への直接 push 禁止・コンフリクトマーカー検出)を有効化する。
エージェント(Claude Code / Codex)・人間の手作業を問わず git 層で強制される。

## コマンド

- 構造検証: `bash scripts/validate.sh`(Skill規約・パス参照・installer・git hooks の動作)
- 対象プロジェクトへの導入: `./install.sh <対象プロジェクトのパス>`

## ルール

- Secrets やローカル環境固有の状態をコミットしない。
- `main` へ直接 push しない。変更は PR 経由で反映する(`.githooks/pre-push` でブロックされる)。
- コンフリクトマーカーを残したまま作業を終えない(`.githooks/pre-commit` でブロックされる)。
- `.claude/hooks/` は Claude Code 利用時の追加の防御層(main への push ブロック・終了時検証)。
  強制の正本は `.githooks/` と GitHub の branch protection。
