---
task_id: T-031
epic: grounding-oracle
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-030]
---

# T-031: human reviewフロー + source grounding gate配線

## 目的

LLM生成候補(`status: draft` かつ `requires_human_review: true` のartifact)を人間が承認・修正・却下できるフローを作り、承認済みartifactのみが後続workflowへ進むことを保証する。計画§7の「候補生成+人間レビュー必須」の実装形であり、以降の全skill(T-032のOracleSpec付与、T-038のStateModel生成等)が「review済み入力」を前提にできるようになる。あわせてblock対象gateのうちsource grounding gateを実フローに配線する(oracle gateの配線はOracleSpecが揃った後、T-054で行う)。

## 参照

- 計画: §6(Gate段階方針: block開始4 gateのうちsource grounding)、§7(候補生成+人間レビュー必須)
- North Star: §6.1(status / requires_human_review)、§17.0(段階的enforcement)、§17.1(gate種別)、§21 Week 2(human review UI/PR comment)

## DoD

- [ ] `status: draft` かつ `requires_human_review: true` のartifact一覧を提示し、承認(`status: reviewed` へ遷移)/ 修正 / 却下を記録できる(最小実装でよい: PR commentでもローカルCLI+レビューファイルでも可。個人開発の実態に合わせて選び、選択理由をタスクに記す)。statusは§6.1のenum(`draft` / `reviewed` / `approved` / `deprecated`)のみを使い、独自status値を発明しない
- [ ] review判断(誰が・いつ・どの判断か)がartifactまたは付随recordに保存され、後から追跡できる
- [ ] 未承認(`draft`)のartifactを入力にした後続skill実行がエラーになる(テストで実証)
- [ ] source grounding gate(source_refsなしblock)が `policies/gate-policy.yaml` の定義どおり実フローで発火する(block発火のテストまたは実行記録)。§17.4のとおり変更対象のP0/P1に限定する
- [ ] gate発火結果が追跡可能な記録として残る(GateDecision schema化と全gateの統合配線はT-054。ここでは暫定記録でよい)

## 検証方法・根拠

<完了時に記入: レビュー実施記録、gate発火の実証>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
