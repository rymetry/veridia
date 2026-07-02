---
description: 指定Phaseの計画mdからタスクファイル群と_index.mdを生成する
argument-hint: <Phase番号 例: 0>
---

Phase $ARGUMENTS の計画を詳細タスクへ分解してください。

## 前提の読み込み(順に)

1. `AGENTS.md`
2. `docs/tasks/README.md` と `docs/tasks/_template.md`
3. `docs/plan/phase-$ARGUMENTS-*.md`(必要ならNorth Starの該当§)

## 手順

1. 計画のワークストリーム(epic ID)ごとにタスクを洗い出す
2. `docs/tasks/phase-$ARGUMENTS/T-<3桁連番>-<slug>.md` を `_template.md` に従って作成する(statusはすべてnot_started)
3. 依存があるタスクはfrontmatterの `blocked_by` に記載する
4. `docs/tasks/phase-$ARGUMENTS/_index.md` をfrontmatterから生成する

## 粒度ルール(§21の指示に従う)

- Week・epic見出しをそのまま巨大タスクにしない。schema定義 / validator / storage / runner / gate wiring等は別タスクに切る
- 1タスク = 1セッションで完了できる規模を目安にする
- DoDは検証可能な形で書く(「〜できる」には検証方法を添える)
- タスク本文にNorth Starや計画の内容を複製しない。`plan_ref` と§参照で示す

## 完了前チェック

- 計画の完了条件チェックリストの各項目が、少なくとも1つのタスクでカバーされているか確認する。カバーされない項目があれば作成を止めて報告する
- epic IDが計画mdに定義されたものと一致しているか確認する
