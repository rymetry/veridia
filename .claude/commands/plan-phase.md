---
description: North Star §20に基づき、指定Phaseの実装計画mdを作成する
argument-hint: <Phase番号 例: 2>
---

Phase $ARGUMENTS の実装計画を作成してください。

## 前提の読み込み(順に)

1. `AGENTS.md`(変更ルール・構成マップ)
2. `docs/plan/00-overview.md`(Phase status、未決事項、依存関係)
3. `docs/qa-agent-strategy.md` §20の該当Phase(+そこから参照される関連§)
4. 直前Phaseの計画md(完了条件チェックリストの充足状況を確認)

## 作成物

`docs/plan/phase-$ARGUMENTS-<slug>.md`。既存のphase-0 / phase-1と同じ章構成にする:

1. 目的とスコープ(やらないことを明記)
2. 完了条件(§20の完了条件を検証可能な形に具体化したチェックリスト)
3. ワークストリーム分割(タスクが使うepic IDを定義)
4. 依存と着手順序
5. 技術選定(ADR起票が必要な決定の列挙。決定はしない)
6. リスクと未確定事項(新規の未決事項はOQ-nnとして採番)
7. タスク分解方針

## ルール

- North Starの内容を複製しない。§番号で参照する(AGENTS.md変更ルール2)
- 直前Phaseの完了条件が未充足の場合、計画作成を進める前にその旨を報告して指示を仰ぐ
- 対象Phaseより先のPhaseを詳細化しない(just-in-time、§5.4.1の思想)
- 完了後に `00-overview.md` を更新する: Phase一覧のstatus(not_started)、未決事項集約表へのOQ追記
- 計画時点で決められないことは隠さず「未確定事項」に明示する
