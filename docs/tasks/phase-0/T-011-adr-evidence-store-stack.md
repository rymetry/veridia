---
task_id: T-011
epic: evidence-trace-store
plan_ref: phase-0-foundation.md#5-技術選定adr起票が必要な決定
status: not_started
owner:
blocked_by: [T-001]
---

# T-011: ADR起票 Evidence Store / Trace Store構成決定

## 目的

OQ-3(Artifact DB / object storeのローカル開発構成)をADRで確定する。WS-Bの実装タスク(T-013 / T-014)の前提。ADR番号は起票時に採番する。

## 参照

- 計画: §5 技術選定、§6 リスクと未確定事項(OQ-3)
- North Star: §15(Trace / Evidence設計)、§22(技術スタック案)

## DoD

- [ ] `docs/decisions/` にADRが存在し、statusがaccepted(人間の承認を得る)
- [ ] metadata DB / object storageのローカル開発構成と、Trace StoreとEvidence Storeの分離方針(§15.1)の実装方式が決定されている
- [ ] `docs/plan/00-overview.md` のOQ-3行が決定済み(ADRへのリンク付き)に更新されている

## 検証方法・根拠

(完了時に記入。想定: ADRファイルの存在とstatus、00-overview.mdの更新を確認)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
