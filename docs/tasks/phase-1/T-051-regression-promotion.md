---
task_id: T-051
epic: execution-evidence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-050]
---

# T-051: regression promotion(W19: human review後のCI test昇格)

## 目的

検証済みの生成テスト・defect再現テストを、human review後に対象repoのCI regression testへ昇格するフローを実装する(W19)。Phase 1完了条件「人間review後にCI testとして昇格できる」をカバーする。

## 参照

- 計画: §5(execution-evidence)
- North Star: §7.3(regression-promotion)、§4.3([H] Promotion)、§26(Regression Promotionの昇格前チェック)、§27.1(Block rules)

## DoD

- [ ] 昇格候補(sandbox実行でpass済み・review承認済みのテスト)から、対象repoへのregression test追加PR(またはpatch)を生成できる(実行記録あり)
- [ ] 昇格前に§26のチェックが実施され記録されている: 既存テストで再現できないことの確認(duplicate防止、T-036の検出を利用)、deterministic oracleの付与
- [ ] 昇格がhuman review承認なしに実行されないことがテストで実証されている(自動mergeしない。PRを作るところまで)
- [ ] 昇格したテストのTestAssetIndexエントリが更新され、昇格由来であることと元のDefectCandidate / 要求への参照が追跡できる(TestAssetIndex schemaに適切なfieldがない場合は、schema拡張の要否を判断してから進める。勝手にfieldを発明しない)
- [ ] 昇格履歴(いつ・何を・どのevidenceを根拠に)が追跡できる記録として残る

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
