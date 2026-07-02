# Phase 1: CRUD/業務アプリMVP 実装計画

対応: North Star §20 Phase 1、§21 Week 2〜4、§31(最終提案)
status: not_started(正本は [00-overview.md](00-overview.md))
前提: Phase 0の完了条件がすべて満たされていること。

## 1. 目的と対象

§4.3 Canonical Quality Workflow(W1〜W19)を、実在する1サービス・1〜2機能に対してend-to-endで最小実装する(§20 Phase 1)。

**対象サービス・機能: 未確定(OQ-2)。Phase 1着手前に決定し、ここに記載する。** 選定基準: 状態遷移が明確(CRUD+状態)、DB/API/eventの観測点にアクセス可能、P0/P1要求が存在する。

## 2. 完了条件

§20 Phase 1の完了条件13項目を正とする(複製しない)。Phase完了レビュー時に§20を開き、各項目へ根拠(タスク・evidence)をリンクしたチェックリストをこの節に追記して判定する。

## 3. 実装するAgent / Skill

§20 Phase 1の表(P0/P1優先度付き)を正とする。実装順はworkflow順(§4.3)に従い、P0を先行する。

## 4. Canonical Workflowマッピング

W1〜W19(§4.3)のうち、Phase 1で最小実装する範囲:

- W1〜W3(Grounding & Impact)、W4〜W5(Test Asset Intelligence)、W6〜W8(Quality Modeling)、W9〜W12(Planning / Generation)、W14〜W15(Execution & Evidence)、W16〜W18(Reporting & Gate)、W19(Promotion)
- W13(性能リスク検出)はStretch扱い(§21 MVPスコープ注記)。release gate必須条件にしない

## 5. Epic分解(§21 Week 2〜4対応)

| epic ID | 対応 | 内容 |
|---|---|---|
| `grounding-oracle` | Week 2 | Source Grounding / QA Analyst / Oracle & Evaluation Agent、validator、PR comment(human review) |
| `test-asset-reuse` | Week 2 | existing-test-discovery / test-reuse-analysis / duplicate-test-detection |
| `modeling-generation` | Week 3 | StateModel / TestabilityReport / API・Playwrightテスト生成 / fixture |
| `quality-intelligence` | Week 3 | change-impact-analysis / test-impact-selection / coverage-gap-detection |
| `execution-evidence` | Week 4 | sandbox実行 / state diff capture / Failure Triage / regression promotion |
| `reporting-gate` | Week 4 | quality-analytics-snapshot / release-readiness-reporting / Gate Report / Dashboard最小版(§18.4 Step 1〜2の範囲) |

## 6. Gate段階方針(§17.0適用)

- block開始: source grounding / oracle / evidence / security の4 gateのみ。かつ変更対象のP0/P1に限定(§17.4 grandfathering)
- shadow開始: change impact / test impact / coverage gap / reuse・dedup系gate。precisionを計測し(§19.7)、昇格条件(shadow 4週間以上 + precision 90%以上)を満たすまでblockしない
- gate段階の正本は `policies/gate-policy.yaml`。変更時はCHANGELOGと `docs/knowledge/calibration/` へ記録

## 7. リスクと未確定事項

- OQ-2(対象サービス)未決。**Phase 1の最初のタスクはこの決定**(ADR不要、本ファイルに記載)
- OQ-4: 対象プロダクトrepoへのSource Connector最小構成(GitHub PR diff取得のみで開始するか)
- LLM出力の品質が不明のため、Week 2の要求・リスク抽出は「候補生成+人間レビュー必須」から始める(§17.0のshadow思想をskill出力にも適用)
- 4週間はcalendar timeの目安ではなくepic規模の目安として扱う(個人開発のため)
