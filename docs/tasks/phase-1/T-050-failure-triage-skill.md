---
task_id: T-050
epic: execution-evidence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-027, T-048]
---

# T-050: `failure-triage` skill(W15: 失敗5分類)

## 目的

ExecutionEvidenceを入力に、失敗を product bug / test bug / oracle issue / flaky / env issue に分類し、再現手順付きDefectCandidateを生成するskillを実装する(W15)。Phase 1完了条件「失敗を5分類できる」をカバーする。

## 参照

- 計画: §5(execution-evidence)
- North Star: §7.3(failure-triage)、§4.3(W15)、§25(失敗分類の正本。Phase 1の5分類は§25の部分集合であり、分類名は§25の正式名に合わせる)

## DoD

- [ ] `qa-skills/failure-triage/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] skill runner経由で、失敗したExecutionEvidence(log・state diff含む)を入力に、5分類のいずれか+根拠+再現手順を含むDefectCandidate候補を生成できる(実行記録あり)
- [ ] flaky疑い分類の場合、sandbox再実行(T-048の経路)による確認手順が出力に含まれる
- [ ] 分類が確定扱いにならずhuman review(T-031フロー)を通る
- [ ] DefectCandidateは§6.xにschema定義が無いため、Phase 1では最小の構造化記録(分類・根拠・再現手順・ExecutionEvidence参照)として保存する。§6相当のschemaを勝手に発明せず、schema化の要否をlearning-logへ記録する
- [ ] `evals/` に5分類それぞれの代表caseがあり、fake LLMでの構造検証がpytestでpassする
- [ ] 実際の失敗(意図的に壊したテストまたは実PRの失敗)1件以上で分類を実行した記録がある

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
