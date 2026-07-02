---
task_id: T-013
epic: evidence-trace-store
plan_ref: phase-0-foundation.md#2-完了条件
status: not_started
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

(完了時に記入。想定: 統合テストの実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
