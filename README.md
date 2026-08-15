# repo-template

汎用リポジトリテンプレート。新規リポジトリの初期設定をワンコマンドで完了します。

## 使い方

### 1. テンプレートからリポジトリを作成

```bash
gh repo create my-new-project --template rymetry/repo-template --public --clone
cd my-new-project
```

### 2. セットアップスクリプトを実行

```bash
bash .github/scripts/setup-repo.sh
```

以下が自動で設定されます:

| 設定 | 内容 |
|------|------|
| **LICENSE** | プレースホルダーを実際の年・名前に置換 |
| **SECURITY.md** | リポジトリ URL を自動設定 |
| **Branch protection** | main に PR 必須 + 管理者バイパス |
| **Auto-merge** | 有効化 |
| **Dependabot** | alerts + security updates 有効化 |
| **Actions** | Workflow permissions を Read only に設定 |
| **不要機能** | Projects / Discussions / Wiki を OFF |
| **ブランチ自動削除** | マージ後に自動削除 |

### 3. README と AGENTS.md を書き換える

- このファイルをプロジェクト固有の内容に置き換えてください。
- `AGENTS.md` にプロジェクト概要とコマンドを記載してください。`CLAUDE.md` は
  `AGENTS.md` へのシンボリックリンクなので、Claude Code からも同じ内容が読まれます。

## 含まれるファイル

```
.claude/
  settings.json                        # Claude Code hook 設定
  hooks/
    pre-tool-use-policy.sh             # main への force push をブロック
    stop-verify.sh                     # コンフリクトマーカー検出
.github/
  workflows/dependabot-auto-merge.yml  # Dependabot patch/minor 自動マージ
  ISSUE_TEMPLATE/
    bug_report.yml                     # バグ報告テンプレート
    feature_request.yml                # 機能リクエストテンプレート
    config.yml                         # blank issue 許可
  PULL_REQUEST_TEMPLATE.md             # PR テンプレート
  scripts/setup-repo.sh                # GitHub 設定自動化スクリプト
AGENTS.md                              # AI agent 共通 context(プレースホルダー)
CLAUDE.md                              # AGENTS.md へのシンボリックリンク
LICENSE                                # MIT License(英語 + 日本語)
CODE_OF_CONDUCT.md                     # Contributor Covenant(日本語)
SECURITY.md                            # 脆弱性報告ポリシー
CONTRIBUTING.md                        # コントリビューションガイド
.gitignore                             # 基本的な除外ルール
```

## ライセンス

[MIT License](./LICENSE)
