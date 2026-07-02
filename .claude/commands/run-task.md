---
description: 指定タスクをAGENTS.mdの作業フローに従って実行する
argument-hint: <task_id 例: T-001>
---

タスク $ARGUMENTS を実行してください。

## 手順(AGENTS.md作業フロー準拠)

1. `docs/tasks/` 配下から $ARGUMENTS のファイルを見つけて読む。frontmatterの `blocked_by` に未doneのタスクがあれば着手せず報告する
2. `plan_ref` が指す計画節を読む。必要ならNorth Starの該当§を読む
3. frontmatterの `status` を `in_progress` に更新してから実装・検証する
4. DoDの各項目を検証し、タスクの「検証方法・根拠」節に確認方法と結果を記入する
5. 作業で得た知見を記録する(該当がある場合のみ):
   - 対象プロダクトの業務知識 → `docs/domain/<product>/`
   - 運用・プロセスの学び、gate較正の気づき → `docs/knowledge/learning-log.md`(エントリに型を付ける)
   - 設計判断 → `docs/decisions/`(North Starからの逸脱は実施**前**にADR)
6. タスクの「記録」節に記録先リンク(なければ「なし」)を記入し、`status` を `done` に更新する
7. `_index.md` を再生成する

## ルール

- DoD未達・テスト失敗・エラー未解決のまま `done` にしない。進められない場合は `status` を `blocked` にし、理由をタスクファイルに追記して報告する
- `docs/` へ書く内容はredaction必須(secret / PII / 本番データの生値禁止)
- 実装規約(AGENTS.md)が未整備の領域で技術選定が必要になったら、勝手に決めずADRを起票して報告する
- タスクのスコープ外の変更(リファクタリング等)を混ぜない。気づきはlearning-logへ記録して本体は触らない
