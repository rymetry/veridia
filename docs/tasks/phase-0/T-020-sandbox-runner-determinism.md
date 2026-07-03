---
task_id: T-020
epic: sandbox
plan_ref: phase-0-foundation.md#2-完了条件
status: done
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

- DoD 1: `tests/test_sandbox_runner.py::test_runner_executes_sample_test_and_saves_execution_evidence`
  - 検証内容: `SandboxRunner` が一時ディレクトリ配下のsandboxを作成/seedし、allowlistされたsample Python testをsandbox root `cwd` で実行する。実行結果(`pass`、stdout、exit code)と相対path基準state diffをExecutionEvidenceとしてEvidence Storeへ保存し、保存済みpayload / test_result / state_diff / logsを確認する。
- DoD 2: `tests/test_sandbox_runner.py::test_same_sample_test_run_twice_has_same_result_and_state_diff`
  - 検証内容: 同一seed / 同一sample testを2つのclean sandboxで実行し、runごとに変わるIDを除いた結果(`verdict=pass`, `exit_code=0`, stdout/stderr)とstate diffが完全一致することをassertする。比較対象のstate diffは `artifacts/sample-result.json` の追加のみで、absolute path / mtime / inode / permissionを含まない。
- DoD 3: `tests/test_sandbox_runner.py::test_each_run_has_ids_and_can_be_read_from_evidence_store`
  - 検証内容: 各runに `IdFactory.new_trace_context()` 由来の `run_id` / `trace_id` が付与され、2 runで互いに異なることを確認する。`EvidenceStore.get_by_artifact_id` と `EvidenceStore.find_by_trace_id` で保存済みExecutionEvidenceを読み出し、metadata / test_result / state_diffを確認する。
- 実行結果: `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_sandbox_runner.py -q` → `3 passed in 0.32s`

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
