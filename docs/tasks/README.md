# tasks/ — 詳細タスク管理

1タスク=1ファイル。`phase-<N>/T-<3桁連番>-<slug>.md` 形式(例: `phase-0/T-001-adr-language.md`)。テンプレートは [`_template.md`](_template.md)。

## ルール

- **statusの正本は各タスクのfrontmatterのみ**。`phase-<N>/_index.md` は集約ビューで、frontmatterから再生成する(手で編集しない)
- status値: `not_started` / `in_progress` / `blocked` / `done`
- `epic` は計画mdのepic ID、`plan_ref` は計画mdの節を指す
- 並行作業時は `owner` でclaimする
- タスク完了の条件: DoD充足 + 知見の記録(AGENTS.md 作業フロー4)

## _index.md の再生成

frontmatterを集計して task_id / epic / status / blocked_by / タイトルの表を作る。全タスクdone後もPhase完了とは判定しない(計画mdの完了条件チェックリストが正、AGENTS.md変更ルール6)。
