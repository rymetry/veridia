# domain/ — 対象プロダクトのドメイン知識(仮置き場)

QA対象プロダクトの業務知識(状態遷移、業務ルール、暗黙の制約、用語)を記録する。**Quality Knowledge Base(North Star §5.4)稼働までの仮置き場**であり、恒久的な置き場ではない。

## 構成

対象プロダクトごとにサブディレクトリを切る: `domain/<product>/`

## KB移行基準(md⇔KB二重管理を防ぐ)

該当するartifact type(RequirementSpec / StateModel等)がKBに実装され、その知識がartifactとして登録されたら、**mdから該当記述を削除しKBへのポインタに置き換える**。両方に実体を持たない。

## ルール

- 記録はjust-in-time(§5.4.1)。タスクで触れた機能の知識のみ書く。網羅的な棚卸しはしない
- **Redaction必須**: 本番データ・PII・secretの生値を書かない(AGENTS.md変更ルール4)
- 出典(source)を必ず添える(§原則1 Source groundingの文書版)
