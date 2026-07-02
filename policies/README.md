# policies/ — versioned config(GatePolicy等)

システムが読み込む設定の正本を置く。人間向け文書ではない(docsと区別する理由)。Phase 0 WS-Eで着手。

## 置くもの

- `gate-policy.yaml` — gateごとの現在段階(shadow / warn / block)、閾値、承認者(§17)
- `CHANGELOG.md` — GatePolicy変更履歴。§17.2「変更はGatePolicyのversionとして記録」の実装

## ルール

- gateは§17.0の段階的enforcementに従う。初期block gateは4つ(source grounding / oracle / evidence / security)のみ。他はshadowまたはwarnから開始
- 閾値変更は必ず `CHANGELOG.md` に記録し、較正の根拠を `docs/knowledge/calibration/` へ相互リンクする
- 較正前の初期閾値(§17.2)を根拠に恒久的なprocessを固定しない
