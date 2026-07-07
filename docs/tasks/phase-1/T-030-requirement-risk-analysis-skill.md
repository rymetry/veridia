---
task_id: T-030
epic: grounding-oracle
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-029]
---

# T-030: `requirement-risk-analysis` skill(W2: 要求・リスク候補生成)

## 目的

SourceMapを入力に、RequirementSpec / RiskSpec候補を生成するskillを実装する(W2)。計画§7の方針どおり「候補生成+人間レビュー必須」であり、生成物はhuman review(T-031)を通過するまで確定しない。Phase 1完了条件「PR差分から要求・リスク候補をsource付きで生成できる」をカバーする。

## 参照

- 計画: §5(grounding-oracle)、§7(候補生成+人間レビュー必須)
- North Star: §7.3(requirement-risk-analysis)、§6.3(RequirementSpec)、§6.4(RiskSpec)

## DoD

- [ ] `qa-skills/requirement-risk-analysis/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] skill runner経由で、対象repoの実PRのSourceMapを入力にRequirementSpec / RiskSpec候補(priority付き)を生成できる(実行記録あり)
- [ ] 全候補が `source_refs` を持ち、artifact_validatorをpassする(source_refsなしはT-008 validatorがrejectすることを確認)
- [ ] 候補は `status: draft` かつ `requires_human_review: true` で保存され(§6.1のenumに `candidate` は無い。独自status値を発明しない)、human reviewなしに後続workflowで確定扱いされない構造になっている
- [ ] `evals/` にpositive / negative case(negative例: sourceにない要求の捏造検出)があり、fake LLMでの構造検証がpytestでpassする

## 検証方法・根拠

<完了時に記入: 実行記録、テスト結果>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
