# Phase 1: CRUD/業務アプリMVP 実装計画

対応: North Star §20 Phase 1、§21 Week 2〜4、§31(最終提案)
Phaseレベルstatusの正本: [00-overview.md](00-overview.md)(status値はここに複製しない。変更ルール3)
前提: Phase 0の完了条件がすべて満たされていること。

## 1. 目的と対象

§4.3 Canonical Quality Workflow(W1〜W19)を、実在する1サービス・1〜2機能に対してend-to-endで最小実装する(§20 Phase 1)。

**位置づけ(2026-07-07追記):** veridiaは特定プロダクト専用ではなく汎用QAプラットフォームである(対象範囲は§3.1)。本PhaseのCRUD/業務アプリは**最初のreference target**であり、プラットフォームの前提ではない。汎用性は抽象インターフェースの先行設計ではなく、Phase 3(LLM/RAG/AI agent Eval拡張)で2つ目のプロダクト種別が同じ基盤に乗ることで検証する。したがって本Phaseでは:

- 対象プロダクト固有の知識をskill/agent本体に埋め込まない。固有知識はconnector設定と `docs/domain/` に隔離する(§5.1 / §5.4の境界)
- CRUD前提がschema・skill・gateへ漏れそうになった箇所を `docs/knowledge/learning-log.md` に記録する(Phase 3対応とNorth Star改訂判断の入力になる)

**対象サービス: veridia自身**(決定 2026-08-02、[T-024](../tasks/phase-1/T-024-target-service-decision.md)。オーナー合意済み)。

**対象機能(2件):**

| # | 機能 | 対象コード | 主要な状態 |
|---|---|---|---|
| F-1 | RunRecordのライフサイクル(skill実行の監査記録を作り、保存し、人間レビューを経て確定する) | `run_store/` / `artifact_validator`(run_record経路) | `status: draft → reviewed → approved` × `requires_human_review` |
| F-2 | ExecutionEvidenceの保存と検索(sandbox実行の証跡をmetadata + blobで残し、trace_idで引く) | `evidence_store/` / `sandbox_runner/` | evidence未収集 / metadata登録済み / blob保存済み |

選定基準(§1)への適合:

- **状態遷移が明確(CRUD+状態)** — F-1は3値のレビュー状態を持つ記録のcreate / read / listであり、CRUD+状態そのもの。F-2はmetadataとblobの2段書き込みで、片側だけ存在する中間状態が実在する
- **DB/API/eventの観測点にアクセス可能** — F-1はJSONファイル(`.veridia/store/runs/`)とRunStore API、およびTrace Storeのrun_metrics record。F-2はSQLite index、blobファイル、`sandbox_runner` のExecutionEvidence。すべてローカルで直接観測でき、seed/clockも固定できる(`sandbox_env`)
- **P0/P1要求が存在する** — F-1「契約を満たさない出力は監査記録にならない」「保存した記録は同一内容で読み戻せる」、F-2「evidenceにsecret/PIIの生値が入らない」(§15.4)はいずれもP0。破れると監査とrelease判断が成立しない
- **対象固有知識を隔離できる** — 対象がveridia自身のため、固有知識は `docs/domain/veridia/` に閉じる。connector設定は不要(OQ-4のSource Connectorはローカルpathで足りる)

**この選定は§1の当初前提からの変更である。** 上の「位置づけ」段落は最初のreference targetとして外部のCRUD/業務アプリを想定していた。veridia自身に替えた理由は、対象固有の立ち上げコスト(connector設定・`docs/domain/` の棚卸し・redaction運用)を後回しにして、W1〜W19の縦通し自体を先に成立させるため。**代償として、CRUD/業務アプリ特有の前提(業務状態遷移、複数ユーザー、UI経路)がW1〜W19で踏まれない。** 汎用性の検証がPhase 3まで持ち越されるのではなく、より手前の「業務アプリで動くか」すら未検証のまま進むことになる。

したがって以下を移行条件とする:

- Phase 1の完了条件(§2)をveridia自身で満たした時点で、**同じW1〜W19を外部の実在サービス1本へ横展開する**。横展開時に必要になった変更は「veridia固有の前提が漏れていた箇所」として `docs/knowledge/learning-log.md` に記録する
- 本Phase中も、CRUD前提およびveridia固有前提がschema・skill・gateへ漏れそうになった箇所は同ログに記録する(既存の指示を対象拡張)

## 2. 完了条件

§20 Phase 1の完了条件13項目を正とする(複製しない)。Phase完了レビュー時に§20を開き、各項目へ根拠(タスク・evidence)をリンクしたチェックリストをこの節に追記して判定する。

## 3. 実装するAgent / Skill

§20 Phase 1の表(P0/P1優先度付き)を正とする。実装順はworkflow順(§4.3)に従い、P0を先行する。

## 4. Canonical Workflowマッピング

W1〜W19(§4.3)のうち、Phase 1で最小実装する範囲:

- W1〜W3(Grounding & Impact)、W4〜W5(Test Asset Intelligence)、W6〜W8(Quality Modeling)、W10〜W12(Planning / Generation)、W14〜W15(Execution & Evidence)、W16〜W18(Reporting & Gate)、W19(Promotion)
- W9(test architecture design)は独立ステップとしては実装しない(§20 Phase 1の表に該当agent / skillが無い)。テスト層の設計判断はテスト生成タスク内で行い、TestArchitectureSpec / TestDesignSpecのschema化はPhase 2以降で判断する
- W13(性能リスク検出)はStretch扱い(§21 MVPスコープ注記)。release gate必須条件にしない

## 5. Epic分解

§21 Week 2〜4に対応する(Weekは§7のとおりcalendar timeではなくepic規模の目安)。

| epic ID | 対応 | 内容 |
|---|---|---|
| `phase1-setup` | 着手前提 | OQ-2(対象サービス)/ OQ-4(Source Connector)の決定、LLM skill実行方式ADR、skill実行基盤最小版 |
| `grounding-oracle` | Week 2 | Source Grounding / QA Analyst / Oracle & Evaluation Agent、validator、PR comment(human review) |
| `test-asset-reuse` | Week 2 | existing-test-discovery / test-reuse-analysis / duplicate-test-detection |
| `modeling-generation` | Week 3 | StateModel / TestabilityReport / API・Playwrightテスト生成 |
| `quality-intelligence` | Week 3 | change-impact-analysis / test-impact-selection / coverage-gap-detection |
| `execution-evidence` | Week 4 | 対象サービスsandbox統合・fixture / sandbox実行 / state diff capture / Failure Triage / regression promotion |
| `reporting-gate` | Week 4 | quality-analytics-snapshot / release-readiness-reporting / Gate Report / Dashboard最小版(§18.4 Step 1〜2の範囲) |

## 6. Gate段階方針(§17.0適用)

- block開始: source grounding / oracle / evidence / security の4 gateのみ。かつ変更対象のP0/P1に限定(§17.4 grandfathering)
- shadow開始: change impact / test impact / coverage gap / reuse・dedup系gate。precisionを計測し(§19.7)、§17.0の昇格条件を満たすまでblockしない。注: Phase 0時点の `policies/gate-policy.yaml` はこれらを `warn` で定義しているため、Phase 1の配線時に `shadow` へ変更しCHANGELOGへ記帳する(T-036 / T-042 / T-043)
- gate段階の正本は `policies/gate-policy.yaml`。変更時はCHANGELOGと `docs/knowledge/calibration/` へ記録

## 7. リスクと未確定事項

- OQ-2(対象サービス)決定済み(2026-08-02、[T-024](../tasks/phase-1/T-024-target-service-decision.md))。veridia自身・2機能。§1参照。**残リスク: 業務アプリ特有の前提がW1〜W19で踏まれない**(§1の移行条件で回収する)
- OQ-4: 対象プロダクトrepoへのSource Connector最小構成(GitHub PR diff取得のみで開始するか)。OQ-2がveridia自身になったため、Phase 1ではローカルpath参照で足りる可能性が高い。横展開時に再評価する
- OQ-5: LLM skill実行方式(provider / model / 呼び出し境界 / コスト管理)未決。Phase 1最初期にADRで決定する
- LLM出力の品質が不明のため、Week 2の要求・リスク抽出は「候補生成+人間レビュー必須」から始める(§17.0のshadow思想をskill出力にも適用)
- 4週間はcalendar timeの目安ではなくepic規模の目安として扱う(個人開発のため)
