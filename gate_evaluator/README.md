# gate_evaluator/ — quality gateの評価とGateDecision生成

`policies/gate-policy.yaml`(§17の正本)を読み、1回のskill runを全gateで評価して
`GateDecision`(§6.24)を出す。T-054の縮小版として、実際にblockできる経路を1本だけ通した実装。

```text
GatePolicy.load() → GateEvaluator.evaluate(run_record) → GateDecisionStore.save()
                                                       → enforce()  # blockでraise
```

## いま評価できるもの

| gate | 状態 | 判定内容 |
|---|---|---|
| `source_grounding` | 実装済み | subjectの `source_refs` に使用可能な参照が1件以上あるか |
| 他15 gate | 未実装 | `inconclusive`(passにはしない) |

`oracle` / `evidence` / `security` は§17.0がblock開始と定める残り3 gateだが、入力を生む
producer(OracleSpec / state diff / SecurityFinding)がPhase 1にまだ無いため未実装。

## 設計上の約束(テストで固定している)

1. **評価器の無いgateは `inconclusive` であって `pass` ではない。** 16/17が未実装の現状で
   passにすると、判定全体が意味を失う。
2. **`inconclusive` はblockしない。** block stageのgateが未実装なだけで全runがblockすると、
   override常態化でgateが形骸化する(§17.0)。代わりに `warn` へ落として可視化する。
   結果として、現在のpolicyでは `decision: pass` は出ない(`test_todays_real_policy_cannot_yield_pass`)。
3. **自己申告 `gate_status` は判定を厳しい側へしか動かせない。** `blocked` はblockさせ、
   `passed-with-risks` はwarnさせるが、`passed` は何も免除しない。信頼ラベルの生成主体と
   ラベルを信頼する主体が同じなら、gateは自己申告で迂回できる(learning-log 2026-08-02)。
4. **shadow stageの判定はrecordに残るだけで判定に影響しない**(§17.0のshadowの定義)。
5. **ruleはsubjectをcontract検証済みとして扱わない。** `RunRecord` schemaは `source_refs` に
   `minItems: 1` を課すため、契約を信じるruleは永遠に発火しない。gateはcontractが通した後の
   独立した2枚目のチェックである。

## モジュール構成

| ファイル | 役割 |
|---|---|
| `policy.py` | `gate-policy.yaml` の読み込みとschema検証。gate → stageのlookup |
| `rules.py` | 実装済みgate ruleのregistry |
| `results.py` | `GateResult` と、stage別の集約ルール(`aggregate`) |
| `evaluator.py` | 全gateの適用、`GateDecision` payload生成、`enforce` |
| `store.py` | GateDecisionのfile保存(1 decision = 1 JSON) |

## 残っているもの(T-054本体)

`oracle` / `evidence` / `security` ruleの実装、shadow gate群のstage変更とCHANGELOG記帳、
ReleaseReadinessReportへの配線(T-053)、gate_precision集計(§19.7)。
