---
task_id: T-013
epic: evidence-trace-store
plan_ref: phase-0-foundation.md#2-完了条件
status: done
owner:
blocked_by: [T-005, T-008, T-011, T-012]
---

# T-013: Evidence Store最小版(保存・読み出しAPI)

## 目的

metadata DB + object storageによるEvidence Store最小版を実装する。計画§2完了条件「test実行結果とstate diffをEvidence Storeへ保存し、読み出せる」をカバーする。

## 参照

- 計画: §2 完了条件、§3 WS-B(Evidence Store最小版)
- North Star: §15.3(保存対象)、§15.4(保存しないもの)、§6.23

## DoD

- [ ] ADR(T-011)で決定した構成のローカル環境が起動でき、手順がREADMEに記載されている
- [ ] ExecutionEvidence(test実行結果 + state diff)を保存し、artifact_id / trace_idで読み出せることが統合テストで実証されている(計画§2完了条件)
- [ ] 保存時にT-008 validatorによるschema検証が実行される
- [ ] §15.4の保存禁止対象(raw secret / PII / raw production data等)の扱いがREADMEに明記されている(機械的検出はPhase 0スコープ外として課題に記録)

## 検証方法・根拠

- ADR(T-011)で決定したローカル構成:
  - 検証方法: `evidence_store/README.md` で追加サービス不要、default root `.veridia/store/evidence/`、pytest時の一時ディレクトリ利用、`evidence.sqlite3` + `objects/` 構成を確認。
  - 結果: READMEに手順と構成を記載済み。
- ExecutionEvidence(test実行結果 + state diff)の保存・artifact_id / trace_id読み出し:
  - 検証方法: `tests/test_evidence_store.py::test_save_and_read_execution_evidence_by_artifact_id_and_trace_id`
  - 結果: `uv run pytest tests/test_evidence_store.py -q` でpass。`artifact_id` / `trace_id` / `run_id` / `test_asset_id` の検索と、test result / state diff / log blobのround-tripを確認。
- 保存時のT-008 validator実行:
  - 検証方法: `tests/test_evidence_store.py::test_save_rejects_invalid_execution_evidence_before_writing_blobs`
  - 結果: `source_refs: []` の不正ExecutionEvidenceが `ArtifactValidationError` で失敗し、blobが書き込まれないことを確認。
- §15.4の保存禁止対象:
  - 検証方法: `evidence_store/README.md` と `docs/knowledge/learning-log.md` のT-013エントリを確認。
  - 結果: raw secret / PII / raw production data / private chain-of-thought等は保存禁止、機械的検出はPhase 0スコープ外で呼び出し側redaction前提、と記録済み。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: `docs/knowledge/learning-log.md` に `2026-07-03 [process-learning] Evidence Store境界のredaction検出はPhase 0では呼び出し側責務として明記する(T-013)` を追加。新規ADRなし(ADR-0003の範囲内)。
