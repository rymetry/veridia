---
task_id: T-029
epic: grounding-oracle
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-026, T-027, T-028]
---

# T-029: `source-grounding` skill(W1: PR diff → SourceMap)

## 目的

対象repoのPR diffと関連ドキュメントから、変更とsourceの対応を示すSourceMapを生成するskillを実装する(W1)。以降の全artifactのsource_refsの根拠となる、workflowの起点。

## 参照

- 計画: §4(W1)、§5(grounding-oracle)
- North Star: §7.3(source-grounding)、§6.2(SourceMap)、§6.1(source_refs必須)、§3.2(sourceなし要求生成の禁止)

## DoD

- [ ] `qa-skills/source-grounding/` がqa-skills/README.mdの新規skill作成手順(1〜8)に従って作成され、registry.yamlに登録されている(既存のmanifest / registry pytestがpass)
- [ ] skill runner(T-027)経由で、T-026のconnectorが取得した対象repoのPR diffを入力に、SourceMap候補(`status: draft`)を生成できる(実行1回の記録: 入力PR、生成物、validator pass)
- [ ] 生成されたSourceMapがT-028 schemaとartifact_validatorをpassする(source_refs必須を含む)
- [ ] `evals/` にpositive / negative caseがあり(negative例: source不明の変更を捏造せずunknownと出す)、fake LLMでの構造検証がpytestでpassする
- [ ] 対象プロダクト固有の知識(サービス名、ドメイン用語の意味づけ等)がSKILL.md・promptにハードコードされていない(固有情報は入力として渡す。計画§1の隔離方針)

## 検証方法・根拠

<完了時に記入: 実行記録、テスト結果>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
