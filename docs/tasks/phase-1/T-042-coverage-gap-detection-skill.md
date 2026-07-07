---
task_id: T-042
epic: quality-intelligence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-032, T-034, T-040]
---

# T-042: `coverage-gap-detection` skill(W10: CoverageGap生成)

## 目的

review済み要求・リスク・OracleSpecと既存テスト資産(TestAssetIndex)を突き合わせ、検証が不足している箇所をCoverageGapとして出すskillを実装する(W10)。「不足分だけ生成する」(T-045 / T-046)の入力になる。

## 参照

- 計画: §5(quality-intelligence)、§6(coverage gap gateはshadow開始)
- North Star: §7.4(coverage-gap-detection)、§6.11(CoverageGap)、§4.3(W10はW7の後: oracleが定義されて初めて不足を判定できる)

## DoD

- [ ] `qa-skills/coverage-gap-detection/` がqa-skills/README.mdの手順に従って作成され、registry.yamlに登録されている
- [ ] skill runner経由で、要求・リスク・OracleSpec・TestAssetIndexを入力に、少なくとも「要求・リスク・oracleの不足」をCoverageGap(severity付き)として生成できる(§21 Week 3のDoD水準。実行記録あり、validator pass)
- [ ] 要求とテストの対応が取れている場合にgapを誤検出しないこと(negative case)がevalsで検証されている
- [ ] `policies/gate-policy.yaml` の `coverage_gap` gateのstageを計画§6(shadow開始)と整合させる(Phase 0時点のpolicyは `warn` のため `shadow` へ変更し、policy version更新とCHANGELOG記帳を行う)
- [ ] coverage gap gateがshadowとして判定を記録する(blockしない。計画§6)
- [ ] fake LLMでの構造検証がpytestでpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
