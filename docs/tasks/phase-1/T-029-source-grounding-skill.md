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
- [x] skill runner(T-027)経由で、T-026のconnectorが取得した変更を入力に、SourceMap候補(`status: draft`)を生成できる(**実LLMで1回実行済み**。下の「実行1回の記録」参照。構造検証は `TestW1EndToEnd` がFakeLLMClientで行う)
- [x] 生成されたSourceMapがT-028 schemaとartifact_validatorをpassする(`source_refs` 必須を含む。契約違反のSourceMapがrecordにならないことも実証)
- [x] `evals/` にpositive / negative caseがあり、fake LLMでの構造検証がpytestでpassする
- [x] 対象プロダクト固有の知識がSKILL.md・promptにハードコードされていない(`TestPackageCarriesNoTargetKnowledge` が禁止語で実証)

## 実装で必要になった判断

**1. 実行経路の一般化。** T-027の実行経路はsqk-core専用で、veridia自前skillの出力は `RunRecord` に載らず `GateDecision` の評価対象にもならなかった。[ADR-0010](../../decisions/adr-0010-handoff-envelope-for-both-contract-families.md) で handoff-envelope を両familyの受け口にし、本タスクでは `SkillSource` Protocol と `QaSkillSource` を足した。

**2. `trust_level` を誰が決めるか。** [ADR-0009](../../decisions/adr-0009-contract-ownership-boundary.md) Decision 2 の実配線。`SkillRunner.run(authoritative_fields=...)` が検証前に上書きする。**「モデルが書いても値が変わらない」ことをテストで固定**した(「上書きする実装がある」では不十分 — 条件付き上書きにすると、モデルが値を書けば自分の値を残せてしまう)。

**3. manifestの出力宣言 → schema_ref の解決。** manifestは成果物をtitle(`SourceMap`)で宣言する。文字列変換ではなく**schemaの `title` との一致**で解決するため、実在しない契約を宣言したmanifestはload時に落ちる。

## 実行1回の記録

**実LLMで1回実行し、記録を取得した(2026-08-02)。**

```bash
uv run python -m source_connector --repo . --label veridia --base 78ef74d~1 --head 78ef74d \
  --change-ref https://github.com/rymetry/veridia/pull/14 --output change.json
uv run python qa-skills/source-grounding/scripts/run_skill.py change.json --agent claude-code
```

| 項目 | 値 |
|---|---|
| 入力 | veridia PR #14(17ファイル / diff 約11k tokens) |
| run_id | `run-20260802T145320462851Z-1a58c48c55d8` |
| 生成物 | SourceMap 1件、`extracted_items` 55件 |
| gate_status | `passed` / `status: draft` / `requires_human_review: true` |
| `sqk_core` pin | 無し(veridia自前skillのため正。ADR-0010 Decision 3) |
| `trust_level` | `trusted`(取り込み層の値。モデル出力ではない) |
| コスト | $0.936(cache_creation 29,437 / output 24,784 tokens) |
| 所要 | 4分26秒 |

**span 55件すべてを実ファイルへ突き合わせて検証した。** 形式違反0 / 変更外path 0 / 行範囲外0。`artifact_id` を採番した項目も0件で、設計した失敗モード(span捏造・ID採番)はいずれも発生していない。

注目すべき自己申告が2点あった。(1) 「作業ディレクトリに対象repoが無いため head_sha のファイル実体と突き合わせていない」— ADR-0005の隔離により**skillは自分のspanを検証できない**。実際の突き合わせはveridia側でしか行えず、validatorを置く自然な場所がここにある。(2) 「`contract_note.py` の第2 hunkのみ再構成した行数がhunkヘッダ申告と1行合わなかったため、spanを広めに取って吸収した」— 誤差を隠さず表明している。

**1回目は失敗している。** 同じ入力で契約検証に全面的に弾かれた(所要4分49秒、記録は0件)。原因と対処は learning-log の2エントリに記録した。呼ぶ手前の門番(ChangeSetが読めない / `source_refs` が空)はテストで固定してある。

## 検証方法・根拠

```bash
uv run pytest tests/test_source_grounding_skill.py -q     # 30 passed
uv run pytest tests/test_portable_schema.py -q            # 14 passed
VERIDIA_REQUIRE_SQK=1 uv run pytest -q                    # 1020 passed
uv run ruff check . && uv run ruff format --check .
```

**mutation checkで防御テストの実効性を確認した。** 意図的な欠陥6件のうち5件を検出、1件(scaffold除外の明示チェック)は**到達不能と判明したため削除**し、代わりに前提(scaffold名がskill名規約に一致しないこと)を固定するテストを置いた。同じ診断は[ADR-0010実装時](../../knowledge/learning-log.md)にも出ている。

検出した5件: `trust_level` を条件付き上書きにする / `authoritative_fields` を無視する / manifestを検証せずload / manifest名とディレクトリ名の不一致を許す / 出力titleを解決せず最初のschemaを返す

## 記録(完了時に記入)

- decisions: [ADR-0010](../../decisions/adr-0010-handoff-envelope-for-both-contract-families.md)(本タスクの前段として起票・実装済み)
- learning-log: [profile内の制約が伝わっているかを誰も確認していなかった](../../knowledge/learning-log.md) / [契約検証で落ちた実行は記録が残らない](../../knowledge/learning-log.md)(いずれも実LLM実測)
- domain: なし(skillは対象非依存。対象固有情報は入力として渡す)
