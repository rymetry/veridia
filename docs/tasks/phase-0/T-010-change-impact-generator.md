---
task_id: T-010
epic: artifact-schema
plan_ref: phase-0-foundation.md#2-完了条件
status: not_started
owner:
blocked_by: [T-006, T-008]
---

# T-010: ChangeImpactSpec候補generator最小版

## 目的

PR diff(git diff)から候補レベルのChangeImpactSpecを生成する。計画§2完了条件「PR diffからChangeImpactSpec(候補レベル)を生成できる」をカバーする。LLM不使用の決定的実装(計画§1のスコープ。§12.5の実装方式が定める決定的な土台に相当する部分のみで、LLMによる意味的マッピング補完はPhase 1以降)。

## 参照

- 計画: §2 完了条件
- North Star: §6.9、§12.5(実装方式と決定的フロア)

## DoD

- [ ] git diff(またはPR diff相当の入力)から、影響ファイル・componentの候補を含むChangeImpactSpec JSONを生成できる(サンプルdiffで実行して確認)
- [ ] 生成物がT-008 validatorをpassする(テストで実証)
- [ ] 候補レベルであること(requirement / riskへのマッピングはPhase 1以降)がconfidence等のfieldまたはREADMEで明示されている

## 検証方法・根拠

(完了時に記入。想定: サンプルdiffに対する生成結果とvalidator結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
