# .claude/commands/ — 作業コマンド

このリポジトリの定型ワークフローをコマンド化したもの。Claude Codeで `/コマンド名 引数` として実行する。
各コマンドはAGENTS.mdの規約を作業手順に展開したプロンプトである。

## ワークフローとコマンド対応

```
/plan-phase <N>      計画作成    North Star §20 → docs/plan/phase-N-*.md
      ↓
/create-tasks <N>    タスク分解  計画のepic → docs/tasks/phase-N/T-xxx.md + _index.md
      ↓
/run-task <T-xxx>    タスク実行  実装 → DoD検証 → 知見記録 → status更新 ←┐
      ↓                                                                 │不合格なら
/task-review <T-xxx> タスク検収  DoD再検証 → 合格/差し戻し → 次タスク提示 ─┘差し戻し
      ↓ (全タスク消化後)
/phase-review <N>    完了判定    完了条件チェックリストを根拠付きで検証 → 次Phaseへ
```

| コマンド | 用途 | 引数 |
|---|---|---|
| `/plan-phase` | 指定Phaseの実装計画mdを作成。直前Phase未完なら停止 | Phase番号 |
| `/create-tasks` | 計画をタスクへ分解。完了条件のカバレッジ検証付き | Phase番号 |
| `/run-task` | タスクを作業フロー通りに実行。DoD未達でdoneにしない | task_id |
| `/run-task-codex` | run-taskのCodex実装×Claude検収分業版(検収内蔵のため/task-reviewは任意) | task_id [--fast] |
| `/task-review` | doneタスクを独立検収。自己申告を信用せず再実行で裏取りし、不合格は差し戻す。次の着手可能タスクを提示(run-taskとのループ用) | task_id |
| `/phase-review` | Phase完了を完了条件チェックリストで判定(タスク消化では判定しない) | Phase番号 |

## 保守ルール

- **規約の正本はAGENTS.mdと各README**。コマンドはその作業手順への展開なので、AGENTS.mdの変更ルールや作業フローを変更した場合は、ここのコマンドも追従させること(乖離すると静かに規約が破られる)
- コマンドはClaude Code用(`.claude/commands/`)。Codexを併用する場合は同内容を `~/.codex/prompts/` へ展開する
