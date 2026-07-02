# knowledge/ — 実運用からの学び

North Star改訂の唯一の入力(North Star冒頭 Document status参照)。

## 構成

- `learning-log.md` — 学びの時系列ログ。エントリには型を付ける
- `calibration/` — gate較正の記録。`policies/CHANGELOG.md` と相互リンクする

## エントリの型

| 型 | 内容 | 行き先 |
|---|---|---|
| `gate-calibration` | gate precision、false block、閾値変更の根拠(§17.2、§19.7) | calibration/ に詳細、logに要約 |
| `domain-insight` | 対象プロダクトの業務知識の発見 | 要約のみ。実体は domain/ へ |
| `process-learning` | 開発・運用プロセスの学び | log |
| `northstar-proposal` | North Star改訂の提案(実測データ・実装上の発見に基づくもののみ) | log → 人間承認 → 改訂 |

## ルール

- 相対日付を書かない(「先週」ではなく日付)
- Redaction必須(AGENTS.md変更ルール4)
