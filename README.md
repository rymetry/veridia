# Veridia

開発の各フェーズに品質の観点を持ち込むための、**対話型Skill+テンプレート**のハーネス。

Skillは成果物の自動生成装置ではない。人間と対話しながらMarkdown成果物を一緒に作り、
上流(PRD等)へフィードバックを返す相棒である。設計思想と運用の全体は
[docs/operating-model.md](docs/operating-model.md) にある。

## 導入

このリポジトリの `skills/` と `templates/` が正本。対象プロジェクトへは installer で導入する。

```bash
./install.sh <対象プロジェクトのパス>
```

導入されるもの:

| 配置先 | 内容 | 再実行時 |
|---|---|---|
| `<対象>/.claude/skills/` | Skill 16本(references 含む) | 常に正本と同期(上書き) |
| `<対象>/quality/templates/` | 成果物テンプレート7枚 | 既存ファイルは保持(`--force-templates` で上書き) |
| `<対象>/quality/operating-model.md` | 運用モデル | 同上 |
| `<対象>/CLAUDE.md` | 前提規律へのポインタ(マーカーブロック) | installer が同期 |

テンプレートと運用モデルはプロジェクト側で書き換えてよいため、既定では上書きしない。
Skillは正本(このリポジトリ)で管理し、更新したら installer を再実行して配る。

導入後、対象プロジェクトの Claude Code で `/premortem` から始める。
成果物(premortem.md、test-plan.md 等)は `quality/` 配下に保存される。

## フェーズ

```text
① プレモーテム → ② 品質特性 → ③ テスト計画 → ④ テストアーキテクチャ
→ ⑤ テスト設計 → ⑥ テストケース(+探索的テストを⑤⑥と並行)
```

各フェーズの成果物は上流(PRD等)へのフィードバックを持ち、修正→再レビューのループを回す。
特定領域(性能・セキュリティ・モバイル等)はドメインSkill 8本が観点を持ち込む。
詳細は [docs/operating-model.md](docs/operating-model.md)。

## 構成

```text
skills/                  対話ガイド16本(フェーズ6+横断1+ドメイン8+GenAI規律1)
  <name>/SKILL.md          毎回の対話で使う手順・問いかけ(100行以内)
  <name>/references/       条件付きで引く資料(シラバス精読ノート・チェックリスト等)
templates/               成果物の雛形7枚
docs/operating-model.md  運用モデル(正本)
install.sh               対象プロジェクトへの導入
scripts/validate.sh      構造検証
```

## 開発(このリポジトリ自体)

構造の検証(Skill規約・パス参照・installer の動作)は次で行う。

```bash
bash scripts/validate.sh
```
