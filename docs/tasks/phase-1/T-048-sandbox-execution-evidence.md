---
task_id: T-048
epic: execution-evidence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-045, T-046, T-047]
---

# T-048: 生成テストのsandbox実行 + ExecutionEvidence保存(W14)

## 目的

review済み生成テスト(T-045 / T-046)を対象サービスのsandbox上で実行し、結果をExecutionEvidenceとしてEvidence Storeへ保存する(W14)。Phase 1完了条件「sandboxで実行できる」をカバーする。

## 参照

- 計画: §5(execution-evidence)、§6(evidence gateはblock対象)
- North Star: §5.7、§6.23(ExecutionEvidence)、§15.3(Evidence Storeの保存対象)
- Phase 0: T-013(Evidence Store)、T-020(runner determinism)

## DoD

- [ ] 生成APIテストを対象サービスのsandbox上で実行し、pass / failがExecutionEvidence(run_id / trace_id付き)としてEvidence Storeへ保存される(実行記録あり、validator pass)
- [ ] 同一テストを2回実行して同一結果になる(T-020の決定性検証を対象サービスで再現)
- [ ] 実行log・テスト出力がevidenceのblobとして保存され、後から読み出せる(テストで実証)
- [ ] evidence欠落(保存失敗)時に実行が黙って成功扱いにならない(文脈付きエラー。evidence gateの前提)
- [ ] Playwrightテスト(T-046)も同じ経路で実行・保存できる(happy path 1本の実行記録)

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
