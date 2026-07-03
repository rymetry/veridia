---
task_id: T-011
epic: evidence-trace-store
plan_ref: phase-0-foundation.md#5-技術選定adr起票が必要な決定
status: done
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

- [x] `docs/decisions/` にADRが存在し、statusがaccepted(人間の承認を得る)
- [x] metadata DB / object storageのローカル開発構成と、Trace StoreとEvidence Storeの分離方針(§15.1)の実装方式が決定されている
- [x] `docs/plan/00-overview.md` のOQ-3行が決定済み(ADRへのリンク付き)に更新されている

## 検証方法・根拠

- オーナー承認に基づき、`docs/decisions/adr-0003-evidence-trace-store-stack.md` のstatusを `accepted` に更新した(採択日: 2026-07-03)。
- ADR-0003のDecision節に、移行コスト最小化の実装制約を追記した:
  - metadata DBのSQLはPostgreSQL互換の範囲に限定し、SQLite固有機能・SQLite方言に依存しない。
  - blobのlogical refは `object-storage://<store>/<run_id>/<object_name>` 形式のS3風URIとし、bucket/keyへ1:1で写像できる構造にする。
  - blob store adapter interfaceはS3セマンティクス(`put` / `get` / `list`)で定義する。
  - Phase 1以降のPostgreSQL / S3互換storage移行時の差し替え対象は、metadata repository adapterとblob store adapterに局所化する。
- `docs/plan/00-overview.md` のOQ-3行を決定済み(2026-07-03)に更新し、ADR-0003へリンクした。
- T-013はADR-0003に従い、ExecutionEvidence metadataをSQLiteへ、test result / state diff / logs等をS3風logical ref付きblobへ保存・読み出しする前提で実装できる。
- T-014はADR-0003に従い、tool call / error / run metricsのredacted trace recordをrun_id / trace_id付きでSQLiteへ保存・時系列照会する前提で実装できる。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: [ADR-0003](../../decisions/adr-0003-evidence-trace-store-stack.md)。domain / learning-log への追加記録はなし。
