---
task_id: T-019
epic: sandbox
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-018]
---

# T-019: fixture seed機構とdeterministic clock

## 目的

sandbox内の初期データを明示的にseedし、時刻依存を固定する。同一test再実行の決定性(T-020)の前提。

## 参照

- 計画: §3 WS-D
- North Star: §5.7(Seeded fixtures / Deterministic clock)

## DoD

- [ ] seed定義(ファイル形式)からfixtureをsandboxへ投入できる(実行ログで確認)
- [ ] reset → 再seedで同一状態になることがテストで実証されている(状態のhash比較等)
- [ ] sandbox内で現在時刻が固定され、2回の実行で同一時刻を返すことがテストで確認されている

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
