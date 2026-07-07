---
task_id: T-027
epic: phase1-setup
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-025]
---

# T-027: skill実行基盤最小版(skill runner)

## 目的

qa-skills packageを読み込み、LLMを呼び出し、出力をartifact schemaで検証し、trace付きで保存する共通実行基盤を作る。Phase 1の全LLM skill(T-029, T-030, T-031, T-035, T-036, T-038, T-039, T-041, T-042, T-043, T-050)がこの上で動く。汎用基盤であり、対象プロダクト固有の知識を含めてはならない(計画§1)。

## 参照

- 計画: §1(固有知識の隔離)、§7(候補生成+人間レビュー必須)
- North Star: §7.1(skill package構造)、§7.5(Skill loop)、§15.1〜15.2(Trace)、ADR-0005(T-025で作成)

## DoD

- [ ] `skill_runner/`(または相当モジュール)で、skill ID を指定して以下が1回の実行で行われる:
  1. `qa-skills/<skill-id>/` のmanifest / SKILL.md / input・output schemaを読み込む
  2. 入力をinput schemaで検証する(fail fast)
  3. ADR-0005の方式でLLMを呼び出す
  4. 出力をoutput schemaおよび該当artifact schemaで検証する(schema不適合は文脈付きエラー。リトライ方針はADR-0005に従う)
  5. 生成artifactを `status: draft` かつ `requires_human_review: true`(human review待ち)として保存し、run_id / trace_id付きでtrace recordを残す(prompt・model・パラメータを含む。redaction適用)。statusは§6.1のenumのみを使い、独自status値を発明しない
- [ ] LLM呼び出し部分が差し替え可能な境界(interface)になっており、テストでは録画済み応答またはfakeで決定的にテストできる(実LLMなしで `uv run pytest` がpassする)
- [ ] 実LLMで最低1回実行し、生成artifactがvalidatorをpassした記録がある(スモークテスト。CIには含めない。実skillは未実装の時点なので `qa-skills/_template` ベースのテスト用ダミーskillで行ってよい)
- [ ] 使い方が `skill_runner/README.md` に記載されている(後続skill実装タスクがこのREADMEだけで実装に入れる水準)
- [ ] AGENTS.mdのリポジトリ構成マップに `skill_runner/` の行が追加されている

## 検証方法・根拠

<完了時に記入: テスト結果、スモークテストの記録>

## 備考

過剰設計にしない。workflow orchestration(複数skillの連鎖)はここでは作らない(T-056で最小限のpipelineを別途扱う)。1 skillを1回実行できることだけに集中する。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
