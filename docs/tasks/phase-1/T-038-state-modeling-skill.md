---
task_id: T-038
epic: modeling-generation
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-027, T-031, T-037]
---

# T-038: `state-modeling` skill(W6: StateModel生成)

## 目的

対象機能の状態遷移と不変条件を抽出しStateModelを生成するskillを実装する(W6)。状態ベースQA(§10)の中核入力であり、テスト生成(T-045 / T-046)とoracle定義の土台になる。

## 参照

- 計画: §5(modeling-generation)
- North Star: §7.3(state-modeling)、§6.5(StateModel)、§10.1〜10.2(状態中心の検証)

## DoD

- [ ] `qa-skills/state-modeling/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] skill runner経由で、review済み(T-031承認済み)RequirementSpecと対象のDB schema・APIドキュメント(connectorまたは入力ファイル経由)を入力に、対象機能のStateModel候補(状態・遷移・不変条件)を生成できる(実行記録あり)
- [ ] 生成StateModelがartifact_validatorをpassし、対象機能の主要状態遷移(CRUD+状態)が含まれることを人間reviewで確認した記録がある
- [ ] 対象サービス固有のドメイン知識をSKILL.md・promptにハードコードせず、入力(`docs/domain/` の内容等)として渡している
- [ ] `evals/` にpositive / negative case(negative例: 不変条件の捏造)があり、fake LLMでの構造検証がpytestでpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
