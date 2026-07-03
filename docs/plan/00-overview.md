# 実装計画 Overview

North Star: [`../qa-agent-strategy.md`](../qa-agent-strategy.md)(§20 実装ロードマップに対応)

本ファイルは実装計画の索引。Phaseレベルのstatusと全体像のみを持つ(タスクレベルのstatusは各タスクファイルが正本。AGENTS.md変更ルール3参照)。

## Phase一覧とstatus

| Phase | 計画 | status | 備考 |
|---|---|---|---|
| Phase 0: Foundation | [phase-0-foundation.md](phase-0-foundation.md) | done | 完了判定 2026-07-03。根拠は [phase-0-foundation.md §2](phase-0-foundation.md) の検証記録 |
| Phase 1: CRUD/業務アプリMVP | [phase-1-crud-mvp.md](phase-1-crud-mvp.md) | not_started | §21の4週間MVP BacklogのWeek 2〜4に対応 |
| Phase 2: Oracle Model / Quality Gate強化 | 未作成 | - | 着手前に詳細化(just-in-time) |
| Phase 3: LLM/RAG/AI agent Eval拡張 | 未作成 | - | 同上 |
| Phase 4: Performance Skill導入 | 未作成 | - | 同上 |
| Phase 5: 本格Performance Testing / CI/CD統合 | 未作成 | - | 同上 |
| Deferred: Workflow UX / AgentOps | 作成しない | - | §20の前提条件が満たされた場合のみ検討 |

Phase 2以降の目的・完了条件は§20を参照(ここに複製しない)。詳細計画は各Phase着手の直前に作成する。

## Phase間の主要依存

- Phase 1はPhase 0の完了条件すべてに依存する(特にartifact schema、Evidence Store、sandbox)
- Phase 2のGate強化はPhase 1のgate運用実績(shadow/warn計測、§17.0)に依存する
- Phase 4はPhase 1の `performance-risk-detection` 事前準備(Stretch)の結果を入力とする

## §29 完成形DoD 追跡表

戦略全体の到達判定(§29の25項目)。Phase完了条件とは別軸で、四半期ごとに棚卸しする。

| # | 項目(短縮) | 状態 | 根拠 |
|---:|---|---|---|
| 1 | source grounding | 基盤のみ | validatorが `source_refs` 空/欠落をreject([T-008](../tasks/phase-0/T-008-artifact-validator.md))。P0/P1要求の実紐付けは未 |
| 2〜4 | OracleSpec / 状態観測点 / MRSpec+EvalTask | 未 | OracleSpec等のschema定義のみ先行([T-004](../tasks/phase-0/T-004-core-spec-schemas.md))。要求への実付与は未 |
| 5 | trial隔離再実行 | 基盤のみ | sandboxで同一test 2回実行→同一結果([T-020](../tasks/phase-0/T-020-sandbox-runner-determinism.md))。agentによるtrial自体は未実装 |
| 6 | Evidence Store保存 | 基盤のみ | state diff・tool call(trace_id付き)・logの保存/読み出しを実証([T-013](../tasks/phase-0/T-013-evidence-store-minimal.md) / [T-016](../tasks/phase-0/T-016-tool-gateway-audit-log.md) / [T-020](../tasks/phase-0/T-020-sandbox-runner-determinism.md))。grader結果は保存fieldのみ(grader未実装) |
| 7〜13 | 失敗分類 / regression昇格 / judge校正 / risk acceptance統制 / skill eval / release3点セット / RiskAcceptance | 未 | GatePolicy設定の§17.1全gate定義のみ先行([T-023](../tasks/phase-0/T-023-gate-policy-minimal.md)) |
| 14 | ChangeImpact生成 | 基盤のみ | PR diffから候補レベル生成([T-010](../tasks/phase-0/T-010-change-impact-generator.md))。requirement / riskへの意味的マッピングは未 |
| 15 | TestAssetIndex | 基盤のみ | repoからindex生成([T-009](../tasks/phase-0/T-009-test-asset-index-generator.md))。「新規生成前に検索する」workflowは未 |
| 16〜19 | reuse判断 / dedup / TestImpactPlan / CoverageGap | 未 | |
| 20 | ReleaseReadinessReport | 基盤のみ | schema定義とvalidation実証([T-007](../tasks/phase-0/T-007-reporting-schemas.md))。実releaseでの生成は未 |
| 21〜24 | Dashboard / performance / workflow自走 | 未 | |
| 25 | Ops追跡 | 部分 | tool errorはaudit logで追跡可(reject時のerror status保存、[T-016](../tasks/phase-0/T-016-tool-gateway-audit-log.md))。skill eval / policy violationの追跡は未 |

達成した項目から行を分割し、根拠(evidence・タスク)をリンクする。

## 未決事項の集約

| ID | 事項 | 決定期限 | 場所 |
|---|---|---|---|
| OQ-1 | 実装言語・スタック(Python/TypeScript、schema lib) | 決定済み(2026-07-02) | [ADR-0002](../decisions/adr-0002-language-schema-lib.md) |
| OQ-2 | Phase 1の対象サービス・機能(1サービス・1〜2機能) | Phase 1着手前 | phase-1 §7 |
| OQ-3 | Evidence Storeの具体構成(DB / object storage) | 決定済み(2026-07-03) | [ADR-0003](../decisions/adr-0003-evidence-trace-store-stack.md) |
| OQ-4 | 対象プロダクトのrepo接続方法(Source Connector最小構成) | Phase 1着手前 | phase-1 §7 |

## 運用メモ

- RACI(§23)は現体制(個人開発)では対象外。チーム運用開始時に `docs/operations/` へ整備する
- 決定記録は `docs/decisions/`(ADR)。本ファイルには書かない
