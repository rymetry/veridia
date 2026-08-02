---
task_id: T-029
epic: grounding-oracle
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: done
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

- [x] `qa-skills/source-grounding/` が新規skill作成手順(1〜8)に従って作成され、`registry.yaml` に登録されている(既存のmanifest / registry pytestがpass)
- [x] skill runner(T-027)経由で、T-026のconnectorが取得した変更を入力に、SourceMap候補(`status: draft`)を生成できる(`TestW1EndToEnd`。実LLMではなくFakeLLMClientでの実証。下の「実行1回の記録について」参照)
- [x] 生成されたSourceMapがT-028 schemaとartifact_validatorをpassする(`source_refs` 必須を含む。契約違反のSourceMapがrecordにならないことも実証)
- [x] `evals/` にpositive / negative caseがあり、fake LLMでの構造検証がpytestでpassする
- [x] 対象プロダクト固有の知識がSKILL.md・promptにハードコードされていない(`TestPackageCarriesNoTargetKnowledge` が禁止語で実証)

## 実装で必要になった判断

**1. 実行経路の一般化。** T-027の実行経路はsqk-core専用で、veridia自前skillの出力は `RunRecord` に載らず `GateDecision` の評価対象にもならなかった。[ADR-0010](../../decisions/adr-0010-handoff-envelope-for-both-contract-families.md) で handoff-envelope を両familyの受け口にし、本タスクでは `SkillSource` Protocol と `QaSkillSource` を足した。

**2. `trust_level` を誰が決めるか。** [ADR-0009](../../decisions/adr-0009-contract-ownership-boundary.md) Decision 2 の実配線。`SkillRunner.run(authoritative_fields=...)` が検証前に上書きする。**「モデルが書いても値が変わらない」ことをテストで固定**した(「上書きする実装がある」では不十分 — 条件付き上書きにすると、モデルが値を書けば自分の値を残せてしまう)。

**3. manifestの出力宣言 → schema_ref の解決。** manifestは成果物をtitle(`SourceMap`)で宣言する。文字列変換ではなく**schemaの `title` との一致**で解決するため、実在しない契約を宣言したmanifestはload時に落ちる。

## 実行1回の記録について

**実LLMでの実行記録は本タスクでは取っていない。** 検証はすべて `FakeLLMClient` による構造検証である。**未達として明示する。**

駆動側は用意した。`qa-skills/source-grounding/scripts/run_skill.py` が ChangeSet JSON を受けて実行し、RunRecord を保存するところまで通っている。

```bash
uv run python -m source_connector --repo . --base HEAD~1 --head HEAD --output change.json
uv run python qa-skills/source-grounding/scripts/run_skill.py change.json
```

実行するとコストが発生し、対象PRの選定も要るため、実行の判断はオーナーに委ねる。呼ぶ手前の門番(ChangeSetが読めない / `source_refs` が空)はテストで固定してある — 空のsourceでLLMを呼ぶとコストだけ払って必ずgateに落ちるため。

## 検証方法・根拠

```bash
uv run pytest tests/test_source_grounding_skill.py -q     # 30 passed
VERIDIA_REQUIRE_SQK=1 uv run pytest -q                    # 1004 passed
uv run ruff check . && uv run ruff format --check .
```

**mutation checkで防御テストの実効性を確認した。** 意図的な欠陥6件のうち5件を検出、1件(scaffold除外の明示チェック)は**到達不能と判明したため削除**し、代わりに前提(scaffold名がskill名規約に一致しないこと)を固定するテストを置いた。同じ診断は[ADR-0010実装時](../../knowledge/learning-log.md)にも出ている。

検出した5件: `trust_level` を条件付き上書きにする / `authoritative_fields` を無視する / manifestを検証せずload / manifest名とディレクトリ名の不一致を許す / 出力titleを解決せず最初のschemaを返す

## 記録(完了時に記入)

- decisions: [ADR-0010](../../decisions/adr-0010-handoff-envelope-for-both-contract-families.md)(本タスクの前段として起票・実装済み)
- learning-log: なし(ADR-0010実装時のmutation checkの学びは同ADRのPRで記録済み)
- domain: なし(skillは対象非依存。対象固有情報は入力として渡す)
