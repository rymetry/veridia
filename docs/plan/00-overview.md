# 実装計画 Overview

North Star: [`../qa-agent-strategy.md`](../qa-agent-strategy.md)(§20 実装ロードマップに対応)

本ファイルは実装計画の索引。Phaseレベルのstatusと全体像のみを持つ(タスクレベルのstatusは各タスクファイルが正本。AGENTS.md変更ルール3参照)。

## Phase一覧とstatus

| Phase | 計画 | status | 備考 |
|---|---|---|---|
| Phase 0: Foundation | [phase-0-foundation.md](phase-0-foundation.md) | not_started | |
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
| 1〜4 | source grounding / OracleSpec / 状態観測点 / MRSpec+EvalTask | 未 | |
| 5〜6 | trial隔離再実行 / Evidence Store保存 | 未 | |
| 7〜9 | 失敗分類 / regression昇格 / judge校正 | 未 | |
| 10〜13 | risk acceptance統制 / skill eval / release3点セット / RiskAcceptance | 未 | |
| 14〜19 | ChangeImpact / TestAssetIndex / reuse判断 / dedup / TestImpactPlan / CoverageGap | 未 | |
| 20〜25 | ReleaseReadinessReport / Dashboard / performance / workflow自走 / Ops追跡 | 未 | |

達成した項目から行を分割し、根拠(evidence・タスク)をリンクする。

## 未決事項の集約

| ID | 事項 | 決定期限 | 場所 |
|---|---|---|---|
| OQ-1 | 実装言語・スタック(Python/TypeScript、schema lib) | Phase 0着手時 | phase-0 §6 / ADR |
| OQ-2 | Phase 1の対象サービス・機能(1サービス・1〜2機能) | Phase 1着手前 | phase-1 §7 |
| OQ-3 | Evidence Storeの具体構成(DB / object storage) | Phase 0 WS-B | phase-0 §6 / ADR |
| OQ-4 | 対象プロダクトのrepo接続方法(Source Connector最小構成) | Phase 1着手前 | phase-1 §7 |

## 運用メモ

- RACI(§23)は現体制(個人開発)では対象外。チーム運用開始時に `docs/operations/` へ整備する
- 決定記録は `docs/decisions/`(ADR)。本ファイルには書かない
