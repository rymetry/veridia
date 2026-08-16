# 品質特性チェック: <プロジェクト名>

- 日付:
- 参加者:
- 入力: PRD <版数> / premortem.md

## 前提

このプロダクトにとって重要な品質特性を**選ぶ**。チェックリストとして全部に
優先度を付けることはしない。選ばなかった特性は理由とともに下の節に残す。

参照フレーム: ISO/IEC 25010:2023 の9特性

```text
Functional Suitability   機能適合性
Performance Efficiency   性能効率性
Compatibility            互換性(相互運用を含む)
Interaction Capability   インタラクション容易性(旧称 Usability)
Reliability              信頼性
Security                 セキュリティ
Maintainability          保守性
Flexibility              柔軟性(旧称 Portability)
Safety                   安全性(2023年版で追加)
```

※ Usability / Portability という旧称(2011年版)を使わない。

## 重要な品質特性

| # | 特性 | 優先度 | なぜ重要か | 関連する失敗シナリオ |
|---|---|---|---|---|
| Q-1 | 例: Reliability | 高 | 通知が唯一の連絡手段になるため | P-2 |
| Q-2 | | | | |

- 関連する失敗シナリオ(P-n)を挙げられない特性は、採用の根拠を対話で確認する

## 上流へのフィードバック

- [ ] 例: PRD に工数削減の測定方法が定義されておらず、達成判定ができない

## 検討したが外したもの

| 特性 | 外した理由 |
|---|---|
| 例: Flexibility | 社内オンプレ固定で移植の要求がない |
