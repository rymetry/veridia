---
description: Phaseの完了条件を検証し、Phase完了を判定する
argument-hint: <Phase番号 例: 0>
---

Phase $ARGUMENTS の完了判定を行ってください。

## 手順

1. `AGENTS.md` → `docs/plan/phase-$ARGUMENTS-*.md` → `docs/tasks/phase-$ARGUMENTS/_index.md` を読む
2. `_index.md` と各タスクfrontmatterの整合を確認する(乖離があれば `_index.md` を再生成)
3. 計画の「完了条件」チェックリストを1項目ずつ検証する。各項目に根拠(タスク、evidence、実際のコマンド実行結果)をリンクする。**「タスクが全部doneだから」は根拠にならない**(AGENTS.md変更ルール6)。検証可能な項目は実際に再実行して確認する
4. 未充足の項目がある場合: 不足を列挙し、必要な追加タスクを提案して停止する。完了と判定しない
5. 全項目充足の場合:
   - 計画mdの完了条件チェックリストに根拠リンクを記入する
   - `docs/plan/00-overview.md` のPhase statusを `done` へ更新する
   - 00-overviewの§29 完成形DoD追跡表のうち、このPhaseで進んだ項目を根拠付きで更新する
   - 00-overviewの「Phase全体像(§20のview)」表がNorth Star §20と乖離していないか照合し、乖離があれば表を§20に合わせて更新する
   - Phaseを通じた学びを `docs/knowledge/learning-log.md` へ記録する(North Star改訂に値する発見があれば `northstar-proposal` 型で起票する)
6. 次Phaseの計画作成(`/plan-phase`)を提案する

## ルール

- 完了判定は保守的に行う。曖昧な充足は「未充足」として扱い、人間に判断を求める
- 根拠リンクのない「充足」を書かない
