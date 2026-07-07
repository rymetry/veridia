---
task_id: T-025
epic: phase1-setup
plan_ref: phase-1-crud-mvp.md#7-リスクと未確定事項
status: not_started
owner:
blocked_by:
---

# T-025: ADR-0005 LLM skill実行方式の決定(OQ-5)

## 目的

Phase 1で初めてLLM駆動のskill(source-grounding、requirement-risk-analysis等)を実装するにあたり、LLM呼び出しの方式を決定しADRとして記録する。Phase 0は決定的実装のみでLLM統合が存在しないため、この決定なしにskill実装(T-027以降)へ進めない。

## 参照

- 計画: §7 リスクと未確定事項(OQ-5、「候補生成+人間レビュー必須」方針)
- North Star: §7.1(skill package構造)、§16.4(QAパイプライン自体の防御)、§15.4(保存しないもの)

## DoD

- [ ] `docs/decisions/adr-0005-llm-skill-execution.md` が作成され、以下が決定されている:
  - provider / model(既定モデルと切替方法。コスト効率のためタスク種別ごとのmodel選択方針を含む)
  - 呼び出し境界(skillからのLLM呼び出しをどのモジュールが仲介するか。Tool Gateway経由か直接かの判断と理由)
  - API key管理(環境変数名。ハードコード禁止、起動時検証)
  - コスト管理(トークン使用量の記録先、上限方針)
  - LLM出力の扱い(構造化出力→schema検証→候補として保存、human review必須の実装形)
  - 再現性の限界の扱い(LLM出力は非決定的である前提で、prompt / model / パラメータをtraceへ記録する方針)
- [ ] 既存ADR(0001〜0004)と同じフォーマット(status / context / decision / consequences)で書かれている
- [ ] `docs/plan/00-overview.md` の未決事項表でOQ-5が「決定済み(日付)」になっている

## 検証方法・根拠

<完了時に記入: ADRへのリンク>

## 備考

決定に際してオーナーの確認を取ること(provider契約・課金に関わるため)。既定候補はClaude API(Anthropic)だが、オーナーの利用可能な契約を確認してから決定する。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
