---
task_id: T-056
epic: reporting-gate
plan_ref: phase-1-crud-mvp.md#2-完了条件
status: not_started
owner:
blocked_by: [T-046, T-051, T-054, T-055]
---

# T-056: W1〜W19 end-to-end実証と完了条件の記帳

## 目的

対象サービスの実PR 1件以上に対してW1〜W19を通しで実行し(W9・W13は計画§4の注記どおり除く)、Phase 1が「end-to-endで最小実装」されたことを実証する。§20 Phase 1完了条件13項目それぞれに根拠(タスク・evidence)をリンクしたチェックリストを計画§2へ追記する(AGENTS.md変更ルール6)。

## 参照

- 計画: §2(完了条件)、§4(Workflowマッピング)
- North Star: §4.3(W1〜W19の順序が正)、§20 Phase 1(完了条件13項目)、§24.1(PR時のworkflow)

## DoD

- [ ] W1〜W8・W10〜W12・W14〜W19を順に実行する最小のpipeline(スクリプトまたは手順書+個別コマンド)があり、対象repoの実PR 1件を入力に最初から最後まで通せる(human reviewステップは人間の操作を挟んでよい)
- [ ] 通し実行のrun_id・生成artifact一覧・最終ReleaseReadinessReport・GateDecisionが記録され、evidenceから全stepを追跡できる
- [ ] §20 Phase 1完了条件13項目のチェックリストが計画§2に追記され、各項目に根拠(タスクID・evidence・実行記録)がリンクされている。**満たせていない項目があれば正直に未達と記載し、doneにしない**
- [ ] 通し実行で得た学び(gate較正、LLM出力品質、CRUD前提の漏れ箇所)が `docs/knowledge/learning-log.md` に記録されている(計画§1: Phase 3対応とNorth Star改訂判断の入力)

## 検証方法・根拠

<完了時に記入>

## 備考

このタスクの完了 = Phase 1完了ではない。Phase完了判定は `/phase-review`(計画mdの完了条件チェックリスト)で別途行う(AGENTS.md変更ルール6)。本タスクはその判定材料を揃えるところまで。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
