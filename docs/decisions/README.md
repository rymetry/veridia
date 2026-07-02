# decisions/ — ADR(Architecture Decision Records)

設計・技術判断、およびNorth Starからの逸脱の記録。`adr-<4桁>-<slug>.md` 形式。

## 最小フォーマット

```
# ADR-0000: タイトル
- status: proposed / accepted / superseded by ADR-XXXX
- date: YYYY-MM-DD

## Context(何を決める必要があったか)
## Decision(何を決めたか)
## Consequences(トレードオフ、影響)
```

## ルール

- North Starからの逸脱はADRを書いてから実施する(AGENTS.md変更ルール5)
- schema・GatePolicyの破壊的変更もADR対象
- 決定の変更は上書きせず、新しいADRで supersede する
