---
task_id: T-018
epic: sandbox
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-002, T-017]
---

# T-018: sandbox ephemeral env(作成・破棄・reset)

## 目的

trialごとに使い捨てられる隔離実行環境の最小版を実装する。fixture(T-019)とrunner(T-020)の土台。

## 参照

- 計画: §3 WS-D、§6(最小実装に留める)
- North Star: §5.7(Ephemeral env / Snapshot・rollback)

## DoD

- [ ] コマンド1発でsandbox環境の新規作成・破棄・resetができる(実行ログで確認)
- [ ] 2回連続で作成(またはreset)した環境が同一の初期状態であることがテストで実証されている(状態のhash比較等)
- [ ] §5.7の要件のうちPhase 0で実装しない項目(network egress control / tenant isolation等)がREADMEにスコープ外として明記されている

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
