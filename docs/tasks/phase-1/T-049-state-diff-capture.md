---
task_id: T-049
epic: execution-evidence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-039, T-048]
---

# T-049: state diff capture(DB / API / event / log差分の保存)

## 目的

テスト実行前後の対象サービスの状態差分(DB / API / event / log)を捕捉しExecutionEvidenceへ保存する。TestabilityReport(T-039)の観測点に基づいて観測する。Phase 1完了条件「DB/API/event/logの状態差分を保存できる」をカバーする。

## 参照

- 計画: §5(execution-evidence)
- North Star: §10.1(状態中心の検証)、§6.23(ExecutionEvidence)、§15.3〜15.4(保存対象とredaction)
- Phase 0: T-020(veridia自身でのstate diff実績)

## DoD

- [ ] T-039のTestabilityReportが列挙する観測点に対して、テスト実行前後のsnapshotを取得しdiffを算出できる(最低限DBとAPI。event / logは対象サービスに存在する範囲で)
- [ ] diffがExecutionEvidenceの一部としてEvidence Storeへ保存され、run_idから読み出せる(実行記録+テストで実証)
- [ ] 観測対象の定義が設定として分離されており、対象サービス固有のテーブル名等がcapture実装にハードコードされていない(計画§1)
- [ ] 保存前にredactionが適用され、secret / PII生値がevidenceに残らない(§15.4。テストで実証)
- [ ] 4種(DB / API / event / log)のうち対象サービスで取得できないものがあれば、理由と扱いをタスクに記録している

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
