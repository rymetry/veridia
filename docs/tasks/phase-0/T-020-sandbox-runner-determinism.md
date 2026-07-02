---
task_id: T-020
epic: sandbox
plan_ref: phase-0-foundation.md#2-完了条件
status: not_started
owner:
blocked_by: [T-013, T-019]
---

# T-020: sandbox test runner最小版と決定性検証

## 目的

sandbox内でtestを実行し、結果をExecutionEvidenceとしてEvidence Storeへ保存するrunner最小版を実装する。計画§2完了条件「sandboxで同じtestを2回実行し、同一結果になる」をカバーし、WS-B/WS-Dを統合した最初のend-to-end動作を実証する。

## 参照

- 計画: §2 完了条件、§3 WS-D
- North Star: §5.7、§6.23、§15.3

## DoD

- [ ] runnerがsandbox内でサンプルtestを実行し、結果とstate diffをExecutionEvidenceとしてEvidence Storeへ保存できる(統合テストで実証)
- [ ] 同一testを2回実行し、結果(pass/fail、state diff)が一致することがテストで実証されている(計画§2完了条件)
- [ ] 各実行にrun_id / trace_id(T-012)が付与され、Evidence Storeから読み出せる

## 検証方法・根拠

(完了時に記入。想定: 統合テストの実行結果、2回実行の比較ログ)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
