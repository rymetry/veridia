---
task_id: T-017
epic: sandbox
plan_ref: phase-0-foundation.md#5-技術選定adr起票が必要な決定
status: done
owner:
blocked_by:
---

# T-017: ADR起票 sandbox実現方式決定

## 目的

sandboxの実現方式(container構成、reset方式、deterministic clockの実現手段)をADRで確定する。WS-Dの実装タスクの前提。ADR番号は起票時に採番する。

## 参照

- 計画: §5 技術選定
- North Star: §5.7(Execution Sandbox)、§22(技術スタック案)

## DoD

- [x] `docs/decisions/` にADRが存在し、statusがaccepted(人間の承認を得る)
- [x] container構成・環境reset方式・時刻固定の実現手段が決定されている
- [x] §5.7の要件表のうちPhase 0で実装する範囲(計画§6: 完了条件を満たす最小実装)がADR内で明示されている

## 検証方法・根拠

- `docs/decisions/adr-0004-sandbox-runtime.md` を作成し、オーナー承認済みのため `status: accepted` に更新した(採択日: 2026-07-03)。
- DoD 1: `docs/decisions/adr-0004-sandbox-runtime.md` が存在し、statusが `accepted` であることを確認した。
- DoD 2: ADR-0004のDecisionで、sandbox実現方式を「Phase 0はprocess + temporary directory based ephemeral env、containerはPhase 1以降へ段階導入」、reset方式を「delete + recreate + state hash」、時刻固定を「`VERIDIA_FIXED_NOW` + clock abstraction」として決定した。
- DoD 3: ADR-0004の「Phase 0で実装する§5.7範囲」で、Ephemeral env / Deterministic clock / Seeded fixtures / Snapshot・rollback最小代替 / No production write最小担保をPhase 0対象とし、network egress control / tenant isolation / resource limit等をPhase 0スコープ外として明示した。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: [ADR-0004](../../decisions/adr-0004-sandbox-runtime.md)
