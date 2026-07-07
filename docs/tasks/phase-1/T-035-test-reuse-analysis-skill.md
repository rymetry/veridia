---
task_id: T-035
epic: test-asset-reuse
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-027, T-031, T-033, T-034]
---

# T-035: `test-reuse-analysis` skill(reuse / extend / new判断)

## 目的

新規テスト意図(要求・リスク)に対して既存テスト資産の再利用可能性を判定し、TestReuseCandidateとreuse / extend / new create判断を記録するskillを実装する(W5前半)。Phase 1完了条件「reuse / extend / new create判断を記録できる」をカバーする。

## 参照

- 計画: §5(test-asset-reuse)
- North Star: §7.4(test-reuse-analysis)、§6.14(TestReuseCandidate)、§13.3(Reuse decision matrix)

## DoD

- [ ] `qa-skills/test-reuse-analysis/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] skill runner経由で、テスト意図(RequirementSpec / RiskSpec)とTestAssetIndexを入力に、TestReuseCandidate(reuse / extend / new の判断と理由付き)を生成できる(実行記録あり)
- [ ] 判断基準が§13.3のdecision matrixに従うことがSKILL.mdに明記され、evals caseで検証されている(§13.3のmatrixは5値。Phase 1は§20完了条件のreuse / extend / new createの3値を判断対象とし、refactor / obsoleteに該当するcaseは判断せず記録のみ残す旨をSKILL.mdに明記する)
- [ ] 判断結果がartifactとして保存され、後から「なぜnewにしたか」を追跡できる(validator pass)
- [ ] `evals/` にpositive / negative caseがあり、fake LLMでの構造検証がpytestでpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
