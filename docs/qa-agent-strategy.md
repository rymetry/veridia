# QAエージェント戦略 完全版プラン 統合版 v3.1

## 安定運用・実運用可能性を最優先した最終設計

**Document status:** North Star(目標アーキテクチャ)。実行計画・タスク分解は別文書で管理する。本書は机上の推敲では改訂せず、実運用からの学び(実測データ・実装上の発見)があった場合のみ改訂する。

**v3.1 変更点(`qa-agent-strategy-v3-review.md` のレビュー反映):**

```text
1. Canonical Quality Workflowを§4.3に新設し、各章の重複workflow定義を参照へ置換(M-3)
2. Gate段階的enforcement(shadow → warn → block)を§17.0に追加(H-3)
3. Source grounding / Oracle gateへのgrandfathering方針を§17.4に追加(H-5)
4. Quality Knowledge Baseへコールドスタート方針(just-in-time modeling)を追加(C-2)
5. Test Impact Selectionの決定的フロアとQAパイプライン自体の防御を追加(H-1 / H-7)
6. confidence非較正の注記、閾値較正メタルール、名称ゆれ等の軽微修正(M-5 / L-1)
```

**統合対象:**

- `QAエージェント戦略 完全版プラン`
- `既存プランに対する改善・修正点のみの追加プラン`

本ドキュメントは、既存の完全版プランを土台に、追加プランで定義された以下の改善点を章構成へ統合した完全版である。

```text
追加統合した主な改善点:
  1. Quality Intelligence
  2. Existing Test Asset Reuse & Deduplication
  3. Quality Analytics & Release Reporting
  4. Quality / Release Readiness Dashboard
  5. Performance Testing Skill
  6. ChangeImpactSpec / TestImpactPlan / CoverageGap / ReleaseReadinessReport 等のartifact
  7. Reuse / Dedup / Performance / Reporting / Change Impact系Gate
  8. 4週間MVP BacklogとPhase Roadmapへの差分反映

維持する既存中核:
  1. Source-grounded Contract
  2. Oracle-first
  3. Isolated Execution
  4. Evidence-by-default
  5. Skill Eval
  6. Human Calibration
  7. Thin Orchestrator
  8. Artifact Contract
  9. Regression Promotion
```

---

# 0. 最終結論

QAエージェント戦略は、**AIにテスト作業を丸投げする構想ではない**。

採用すべき最終方針は、次である。

> **Source-grounded Contract + Oracle-first + Isolated Execution + Evidence-by-default + Skill Eval + Human Calibration + Quality Intelligence + Existing Asset Reuse + Release Readiness**

つまり、すべての要求・リスク・テスト・判定をソースに紐付け、agent間は会話ではなくschema付きartifactで接続し、テストケースより先にオラクルを定義し、実行は隔離環境で再現可能にし、操作・状態差分・判定を証跡化し、skill自体も継続評価し、AI judgeは人間評価で校正する。

今回の統合でさらに、**変更影響、既存テスト資産、重複排除、カバレッジギャップ、性能リスク、リリース準備状況**を品質判断へ接続する。

最終的な主語は、AI Agentの管理ではない。

> **品質・リスク・証跡・リリース判断を、再現可能かつ監査可能にすること。**

したがって、本プランではAgentOps専用画面や自然言語Workflow生成を中核にしない。必要なのは、品質判断のためのartifact、gate、evidence、dashboardである。

---

# 1. 設計原則

## 1.1 QAエージェントの本質

QAエージェントの本質は、**テストケース生成の自動化**ではない。

本質は以下である。

> **オラクル・状態・関係性・証跡を中心にした品質推論ループの自動化**

CRUD / 業務アプリでは、状態遷移、不変条件、DB/API/event/audit logまで含めた検証が必要である。

LLM / RAG / agent型プロダクトでは、単一出力の正解だけに依存せず、metamorphic relation、groundedness、tool call整合性、複合grader、人間校正を組み合わせる。

## 1.2 統合後の12原則

| 原則 | 内容 |
|---:|---|
| 1 | **Source grounding**: すべての生成物をPR、仕様、issue、障害、ログなどのsourceへ紐付ける |
| 2 | **Artifact contract**: agent同士を自然言語ではなくschema付きartifactで接続する |
| 3 | **Oracle first**: テストケースより先に「どう判定するか」を決める |
| 4 | **State for CRUD**: CRUD/業務アプリは状態遷移と不変条件を中心に検証する |
| 5 | **Relation for AI**: LLM/RAG/agentはmetamorphic relationと複合graderで検証する |
| 6 | **Isolated execution**: trialごとに環境、データ、時計、外部依存を分離・固定する |
| 7 | **Evidence by default**: 入力、出力、tool call、状態差分、ログ、grader結果を保存する |
| 8 | **Skill eval**: skillそのものの発火、出力、効率、安全性を評価する |
| 9 | **Human calibration**: AI judgeは補助。高リスク・低確信・主観領域は人間で校正する |
| 10 | **Regression promotion**: AI探索結果は決定的なCI資産へ昇格する |
| 11 | **Reuse before generation**: 新規テスト生成前に既存テスト資産を検索し、再利用・拡張・重複排除する |
| 12 | **Release readiness over agent ops**: agent稼働監視ではなく、品質・リスク・証跡・リリース判断を中心に可視化する |

---

# 2. 外部ベストプラクティスの反映

## 2.1 OpenAIから採用するもの

OpenAIのevals / graders / evaluation best practices / Agents SDKの考え方から、eval harness、grader設計、human calibration、skill eval、tracing、guardrails、handoffsの考え方を採用する。特にEvals APIは評価をprogrammaticに構成でき、gradersは機械的判定やmodel-based判定を組み合わせる前提を支える。([OpenAI][2]) ([OpenAI][3]) ([OpenAI][4]) ([OpenAI Agents SDK][5])

ただし、特定vendorのEvals Platformやgrader APIへ直接依存しない。OpenAI Evals Platformは、既存ユーザー向けに2026-10-31にread-only、2026-11-30にshutdown予定と明記されているため、評価思想は採用しつつ実装はvendor-neutralにする。([OpenAI][2])

採用する実装方針は以下である。

```text
- Eval HarnessをCI/CDとEvidence Storeの中核に置く
- model-based graderだけでなく、機械的graderとcode-based graderを併用する
- AI judgeは最終判定者ではなく、人間校正された判定補助として扱う
- agent runtimeにはhandoff、guardrails、tracing、human-in-the-loopを要求する
- skill変更時にはskill evalを走らせる
```

handoff、guardrail、tracingはOpenAI Agents SDKの設計を参考にするが、handoffが通常のfunction tool pipelineとは異なる扱いになる点も踏まえ、独自のartifact contractとpolicy checkで包む。([OpenAI Agents SDK][13]) ([OpenAI Agents SDK][14]) ([OpenAI Agents SDK][16]) ([OpenAI][15])

## 2.2 Anthropicから採用するもの

Anthropicのagent eval設計から、task、trial、grader、transcript、outcome、evaluation harness、agent harnessを分離する考え方を採用する。graderはcode-based、model-based、humanを組み合わせ、非決定性にはmultiple trials、pass@k、pass^kを使い分ける。([Anthropic][1])

特に重要なのは、agentが「成功しました」と言ったかではなく、**環境上の最終状態が期待通りか**を見ることである。

採用する実装方針は以下である。

```text
- code-based / model-based / human graderを組み合わせる
- 非決定性に対してmultiple trialsを実行する
- 探索系ではpass@kを見てもよいが、customer-facing agentではpass^kを重視する
- 各trialをclean environmentから開始する
- orchestrator-workers workflowとevaluator-optimizer workflowをskill loopに適用する
- skillはSKILL.md、schema、validator、script、eval、failure modesを含む実行可能パッケージにする
```

workflow設計はAnthropicのorchestrator-workers / evaluator-optimizerの整理を参考にし、skill packagingはClaude Code skillsのinvocation control、subagent execution、dynamic context injectionの考え方を参考にする。([Anthropic][6]) ([Claude Docs][7])

## 2.3 標準・研究から採用するもの

ISO/IEC/IEEE 29119のような標準プロセスは否定しない。ISO/IEC/IEEE 29119-2:2021は、任意の組織・プロジェクト・テスト活動でsoftware testingをgovern、manage、implementするためのtest processesを定義し、すべてのsoftware development lifecycle modelsに適用可能である。これをAI時代向けにartifact loopへ写像する。([ISO][8])

テストオラクル問題の知見から、テストケース生成よりも先にOracleSpecを作成する。([Barr et al.][9])

Metamorphic testingの知見から、LLM/RAG/agentのように直接的な期待値が決めにくい対象には、入力変換と出力関係に基づくMRSpecを中核として使う。([Metamorphic Testing Survey][10])

OWASP Top 10 for LLM Applications、OWASP Top 10 for Agentic Applications 2026、AI Agent Security Cheat Sheetの知見から、prompt injection、tool misuse / tool abuse、excessive agency、memory poisoning、情報漏えい、supply chainを全層制約として扱う。([OWASP][11]) ([OWASP][22]) ([OWASP][23])

NIST AI RMFの考え方から、QA結果をpass/failだけではなく、Govern / Map / Measure / Manageに対応するリスク管理成果物へ接続する。([NIST][12])

## 2.4 Tricentis系Quality Engineeringから採用するもの

Tricentis AI Workspace、qTest、SeaLights、NeoLoadの思想から、以下だけを採用する。AI WorkspaceはAI agents、workflows、人間の監督をSDLC横断でorchestrateするcontrol plane、qTestは既存テストのreuse / extend / duplication prevention、SeaLightsはTest Impact Analyticsとcoverage gap、NeoLoadはAgentic Performance TestingとAPM / CI連携を打ち出している。([Tricentis][18]) ([Tricentis][19]) ([Tricentis][20]) ([Tricentis][21])

```text
採用する:
  - Quality Intelligence
  - Analytics / Reporting
  - Existing Test Asset Reuse
  - Duplicate Test Prevention
  - Test Impact Analytics
  - Coverage Gap Detection
  - Performance Testing Skill
  - Release Readiness Dashboard

MVPでは採用しない:
  - 自然言語からWorkflow生成
  - 独立したAgent Registry UI
  - 独立したAgentOps Dashboard
  - 初期からの大規模Performance Testing Agent
```

理由は単純である。今回の目的は、agentを華麗に管理することではなく、**品質判断の精度と説明可能性を上げること**である。

## 2.5 採用判断サマリ

差分プラン側の採用判断を、統合版でも明示しておく。ここを消すと「何を採用し、何を後回しにしたのか」が読み手の脳内会議に委ねられる。人間の脳内会議はだいたい議事録がない。

| 項目 | 採用判断 | 優先度 | 理由 |
|---|---:|---:|---|
| Analytics / reporting | 採用 | P0 | GateDecisionを組織の判断材料に変換する出口になる |
| Quality Intelligence | 採用 | P0/P1 | 変更影響、テスト選択、カバレッジギャップ、Release Readinessを扱うため |
| Performance Testing Skill | 採用 | P1/P2 | 性能リスクを早期検出し、必要なときだけ性能検証へ広げるため |
| Performance Testing Agent | 後続採用 | P2 | 初期はSkillで十分。Agent化は性能検証運用が成熟してから |
| 既存テスト資産の再利用・重複排除 | 採用 | P0/P1 | AIによる重複テスト量産と保守負債を防ぐため |
| Quality / Release Readiness Dashboard | 採用 | P1 | 本格運用で品質・リスク・証跡・リリース判断を可視化するため |
| 自然言語からWorkflow生成 | 不採用 / Deferred | P3以降 | 便利UIだが、今回の品質戦略の中核ではない |
| 独立Agent Registry | 不採用 / Internal only | - | 内部メタデータ管理で十分 |
| 独立AgentOps Dashboard | 不採用 / Dashboard内の一部に吸収 | - | agentではなく品質判断を主役にするため |

内部的には、以下の最小メタデータだけを残す。

```text
- Skill registry
- Skill / Agent ownership
- allowed_tools
- schema_version
- eval_status
- policy_violation_metrics
```

---

# 3. 対象範囲と非対象

## 3.1 対象範囲

| 対象 | 内容 |
|---|---|
| CRUD / 業務アプリ | 画面、API、DB、イベント、監査ログ、外部連携を含む状態ベースQA |
| API / backend | OpenAPI、schema、contract、state diff、不変条件検証 |
| UI / E2E | Playwright等による操作、UI状態、backend状態との整合 |
| RAG / LLMアプリ | groundedness、retrieval scope、引用整合、MR評価 |
| AI agent型プロダクト | tool call、権限、side effect、transcript、outcome評価 |
| セキュリティQA | prompt injection、tool misuse、excessive agency、情報漏えい |
| Quality Intelligence | 変更影響、テスト影響、coverage gap、release readiness |
| 既存テスト資産活用 | test asset indexing、reuse、extend、duplicate prevention |
| Performance Testing | 性能リスク検出、性能シナリオ設計、性能証跡分析、性能gate |
| CI/CD quality gate | リリース判断、残リスク、回帰検出、証跡保存 |
| Release Reporting | GateDecision、ReleaseReadinessReport、Quality Dashboard |

## 3.2 最初からやらないこと

| 非対象 | 理由 |
|---|---|
| 完全自律release承認 | リスク受容は人間・組織責任 |
| 本番write操作 | QA agent自体が障害源になる |
| 全QA工程の一括自動化 | 失敗時に原因分解できない |
| AI judge単独判定 | 非決定的で校正が必要 |
| 毎回LLM自由探索CI | 不安定、高コスト、再現困難 |
| sourceなし要求生成 | 要求捏造の温床 |
| traceなし自動実行 | 失敗時に説明不能 |
| 自然言語からWorkflow生成 | 初期は監査性と再現性を落とす |
| 独立Agent Registry UI | Skill registry metadataで十分 |
| 独立AgentOps Dashboard | Quality / Release Readiness Dashboard内の最小Opsで十分 |
| 初期から大規模load testing自動実行 | まず性能リスク検出とscenario設計から始める |

---

# 4. 全体アーキテクチャ

## 4.1 統合後の推奨アーキテクチャ

```text
[1. Source Connectors]
  - GitHub / GitLab PR / diff
  - Jira / Linear / GitHub Issues
  - 要求仕様書 / 設計書
  - OpenAPI / GraphQL schema
  - DB schema / migration
  - 本番ログ / incident / support ticket
  - RAG corpus / policy documents
  - CI history / test result
  - APM / performance telemetry

        ↓

[2. Ingestion & Normalization Layer]
  - source classification
  - PII / secret redaction
  - document versioning
  - source lineage
  - requirement extraction
  - change impact extraction
  - test result normalization

        ↓

[3. Test Asset Intelligence Layer]
  - existing test asset indexing
  - reuse candidate detection
  - duplicate test detection
  - test gap detection
  - test impact mapping
  - maintenance risk estimation

        ↓

[4. Quality Knowledge Base]
  - RequirementSpec
  - RiskSpec
  - StateModel
  - OracleSpec
  - MRSpec
  - CoverageModel
  - PolicyModel
  - TestabilityReport
  - ChangeImpactSpec
  - TestImpactPlan
  - CoverageGap
  - ReleaseReadinessSignal
  - TestAssetIndex
  - TestReuseCandidate
  - DuplicateTestReport
  - TestGapReport
  - PerformanceRiskSpec
  - PerformanceScenarioSpec

        ↓

[5. Thin Quality Orchestrator]
  - artifact contract validation
  - source grounding enforcement
  - skill selection
  - agent handoff
  - quality gate enforcement
  - budget control
  - human review routing
  - test reuse / dedup gate
  - performance risk routing
  - trace_id / run_id management

        ↓

[6. Skill Runtime]
  - skill registry
  - SKILL.md
  - input/output schema
  - validators
  - scripts
  - examples
  - evals
  - versioning / ownership
  - quality intelligence skills / quality-intelligence skills
  - test asset reuse skills / test-asset-reuse skills
  - performance testing skills / performance-testing skills
  - analytics reporting skills / analytics-reporting skills

        ↓

[7. Specialist Agent Layer]
  - Source Grounding Agent
  - QA Analyst Agent
  - Testability Agent
  - Test Architect Agent
  - Oracle & Evaluation Agent
  - Automation Agent
  - Execution & Evidence Agent
  - Failure Triage Agent
  - Security Agent
  - Release Gate Agent
  - Quality Intelligence Agent
  - Performance Testing Agent later

        ↓

[8. Tool Gateway]
  - browser automation
  - API runner
  - DB verifier
  - event verifier
  - log search
  - RAG evaluator
  - LLM judge
  - code runner
  - security scanner
  - test asset indexer
  - coverage analyzer
  - performance runner later

        ↓

[9. Execution Sandbox]
  - ephemeral environment
  - deterministic clock
  - seed data / fixture
  - mocked external services
  - network egress control
  - no production write by default
  - performance sandbox later

        ↓

[10. Trace & Evidence Store]
  - agent trace
  - transcript / trajectory
  - tool calls
  - state diff
  - screenshots
  - logs
  - grader results
  - human review
  - reproduction bundle
  - QualityAnalyticsSnapshot
  - ReleaseReadinessReport
  - PerformanceEvidence

        ↓

[11. Quality Gate & Reporting]
  - release decision
  - residual risk
  - requirement coverage
  - risk coverage
  - oracle completeness
  - MR coverage
  - flaky rate
  - judge-human agreement
  - cost / latency
  - coverage gap summary
  - test impact summary
  - existing asset reuse summary
  - performance risk summary
  - Quality / Release Readiness Dashboard
```

## 4.2 アーキテクチャ上の重要判断

### Thin Orchestratorは維持する

オーケストレータは、作業手順を細かく支配する巨大司令塔ではなく、artifact contract、quality gate、予算、証跡、人間レビューを調停する薄い制御層とする。

### Test Asset Intelligence Layerを追加する

新規テストを生成する前に、既存テストを検索し、reuse / extend / duplicate / gapを判定する。これにより、AIによる重複テスト量産とE2E過多を防ぐ。

### Quality Intelligenceを追加する

変更差分、要求、リスク、既存テスト、coverage、evidenceをつなぎ、実行すべきテスト、skip可能なテスト、coverage gap、release readinessを判断する。

### DashboardはRelease Readiness中心にする

独立したAgentOps Dashboardは作らない。必要なOps情報は、Quality / Release Readiness Dashboard内の最小Ops sectionに吸収する。

## 4.3 Canonical Quality Workflow

本書には複数の章にworkflowが登場するが、**実行順序の正は本節のみ**とする。他章のworkflow記述はすべて本節のview(抜粋・適用例)であり、順序が食い違う場合は本節を優先する。

```text
[A] Grounding & Impact
  W1  Source grounding                     → SourceMap
  W2  Requirement / Risk extraction        → RequirementSpec / RiskSpec
  W3  Change impact analysis               → ChangeImpactSpec

[B] Test Asset Intelligence
  W4  Existing test asset discovery        → TestAssetIndex(参照・更新)
  W5  Reuse / dedup analysis               → TestReuseCandidate / DuplicateTestReport

[C] Quality Modeling
  W6  State modeling                       → StateModel
  W7  Oracle definition                    → OracleSpec
  W8  Testability analysis                 → TestabilityReport

[D] Planning
  W9  Test architecture design             → TestArchitectureSpec
  W10 Gap analysis                         → TestGapReport / CoverageGap
  W11 Test impact selection                → TestImpactPlan

[E] Generation(不足分のみ)
  W12 Test design & implementation         → TestDesignSpec / TestAsset
  W13 Performance risk detection           → PerformanceRiskSpec(W3完了後いつでも並行可)

[F] Execution & Evidence
  W14 Sandbox execution & evidence capture → ExecutionEvidence
  W15 Failure triage                       → DefectCandidate / FlakyReport

[G] Reporting & Gate
  W16 Quality analytics snapshot           → QualityAnalyticsSnapshot
  W17 Release readiness reporting          → ReleaseReadinessReport
  W18 Human review & gate enforcement      → GateDecision / RiskAcceptance

[H] Promotion
  W19 Regression promotion                 → CI regression test
```

順序に関する設計判断:

```text
- W4/W5(既存資産)はW6以降のモデリングより前に置く。
  既存テストで十分な範囲が分かれば、モデリングと生成のコストを削減できるため。
- W10(gap分析)はW7(oracle)の後に置く。
  「何を検証すべきか」が定義されて初めて「何が不足か」を判定できるため。
- W13(性能リスク検出)は直列必須ではなく、W3完了後いつでも並行実行してよい。
```

---

# 5. コンポーネント詳細

## 5.1 Source Connectors

目的は、AIが勝手に要求やリスクを作らないように、すべての品質判断をsourceへ接続することである。

| Connector | 取得する情報 |
|---|---|
| GitHub / GitLab | PR diff、commit、review comment、test result |
| Jira / Linear | 要求、bug、priority、acceptance criteria |
| Notion / Confluence | 仕様、設計、運用手順 |
| OpenAPI / GraphQL | endpoint、schema、error contract |
| DB migration | table、constraint、state transition候補 |
| Observability | log、trace、metric、incident |
| Support tool | 問い合わせ、苦情、実利用失敗 |
| RAG corpus | 文書version、chunk、source URL、権限 |
| CI history | test result、flake、duration、failure history |
| APM / telemetry | latency、throughput、error rate、resource metrics |

必須処理は以下である。

```text
source ingestion
  ↓
classification
  ↓
PII / secret redaction
  ↓
versioning
  ↓
source lineage assignment
  ↓
artifact candidate extraction
```

## 5.2 Ingestion & Normalization Layer

異なるsourceから取得した情報をartifact化しやすい形へ正規化する。

```text
主な責務:
  - source_type分類
  - source trust label付与
  - PII / secret redaction
  - version固定
  - PR差分と要求・リスクの候補抽出
  - CI履歴とtest asset metadataの正規化
  - performance telemetryの正規化
```

## 5.3 Test Asset Intelligence Layer

新規テスト生成の前段に置く。

```text
責務:
  - 既存テスト資産のindex化
  - 要求・リスク・API・状態モデル・オラクルとの紐付け
  - 新規テスト意図に対する既存テスト候補検索
  - reuse / extend / refactor / obsolete判断
  - duplicate test candidate検出
  - TestGapReport生成
  - maintenance risk評価
```

この層がないと、AIは似たようなテストを量産し、CIを遅くし、保守負債を増やす。テスト自動生成がテスト保守地獄を自動生成してはいけない。

## 5.4 Quality Knowledge Base

QAエージェントが毎回ゼロから世界を解釈しないための知識基盤である。

| Model | 内容 |
|---|---|
| `RequirementSpec` | 要求、受け入れ条件、source、owner、優先度 |
| `RiskSpec` | 影響度、発生可能性、検出可能性、過去障害、規制影響 |
| `StateModel` | entity、state、transition、pre/post condition、不変条件 |
| `OracleSpec` | 判定方法、signals、threshold、grader、人間review条件 |
| `MRSpec` | 入力変換、期待関係、比較方法、対象リスク |
| `CoverageModel` | 要求、リスク、状態遷移、MR、API、UI、security coverage |
| `PolicyModel` | 権限、tenant、PII、tool allowlist、禁止操作 |
| `TestabilityReport` | 観測可能性、制御可能性、リセット可能性、再現可能性 |
| `EvalSuite` | LLM/RAG/agent向け評価セット |
| `GatePolicy` | release blocking条件、threshold、承認者 |
| `ChangeImpactSpec` | PR差分が影響する要求、リスク、API、状態、既存テスト |
| `TestImpactPlan` | 実行すべきテスト、skipするテスト、新規テスト要否 |
| `CoverageGap` | 要求・リスク・oracle・evidence・code単位の不足 |
| `ReleaseReadinessSignal` | release判断の前段信号 |
| `TestAssetIndex` | 既存テスト資産とcoverage / stability / owner情報 |
| `TestReuseCandidate` | 既存テストのreuse / extend / refactor候補 |
| `DuplicateTestReport` | 重複テスト候補と生成block/warn判断 |
| `TestGapReport` | 既存テストで不足している検証観点 |
| `PerformanceRiskSpec` | PR差分から推定される性能リスク |
| `PerformanceScenarioSpec` | 性能検証シナリオ、負荷条件、SLA/SLO |
| `PerformanceEvidence` | 性能検証の実行結果、SLA判定、ボトルネック仮説 |
| `PerformanceGateDecision` | 性能観点のblock / warn / pass判断 |
| `QualityAnalyticsSnapshot` | coverage、execution、evidence、costの集約snapshot |
| `ReleaseReadinessReport` | release候補のreadiness、block/warn理由、承認要否 |
| `ResidualRiskReport` | release時点で残るリスク、影響、受容・期限・owner |
| `RiskAcceptance` | gate override / risk acceptanceの責任者、期限、証跡 |
| `DashboardViewSpec` | dashboard view、refresh policy、access control |

### 5.4.1 コールドスタート方針(just-in-time modeling)

Quality Knowledge Baseは「最初に全体を構築してから運用する」ものではない。初期構築の網羅性を前提にすると構築コストが膨張し、かつ不完全な分母に基づく偽の精度(false precision)がリリース判断を汚染する。

```text
原則:
  - KBはPRが触れた機能から漸進的に構築する(just-in-time modeling)
  - 全機能を対象にしたバッチ構築は行わない
  - 既存機能の棚卸し契機は、変更発生時・incident発生時・
    risk assessmentでの高リスク判定時に限る(§17.4 grandfathering参照)

TestAssetIndexの精度検証:
  - インデックスされた紐付け(test ↔ requirement / risk / oracle)は
    サンプル監査を定期実施する(例: 新規紐付けのN%を人間が検証)
  - 監査精度が閾値未満の間は、TestAssetIndexに依存する下流gate
    (test impact / reuse・dedup)をshadow / warnに留める(§17.0参照)

カバレッジ指標の分母問題:
  - requirement_coverage等の比率は、要求抽出が網羅的である前提でのみ意味を持つ
  - 分母の信頼度(estimated / audited)を指標に併記する
  - 分母が未監査の間は、比率ではなく件数ベース(covered / uncovered件数)で表示する
```

## 5.5 Thin Quality Orchestrator

オーケストレータは「実行順序の支配者」ではなく「品質制御の調停者」として設計する。

| 責務 | 内容 |
|---|---|
| Contract validation | agent/skillの入出力schemaを検証 |
| Source grounding enforcement | source_refsがない生成物をblock |
| Skill selection | artifact状態から必要skillを選ぶ |
| Handoff control | agent間handoffをartifact単位で管理 |
| Budget control | LLM call、token、test runtime、parallelismを制御 |
| Risk routing | 高severity領域を優先 |
| Human routing | 高リスク、低確信、法務、安全、ブランド判断を人間へ |
| Test reuse / dedup enforcement | 新規TestAsset生成前の既存テスト検索を強制 |
| Performance risk routing | 性能リスクがある変更をperformance skillへ送る |
| Gate enforcement | release block条件を機械的に適用 |
| Audit | すべての判断をtrace_idに接続 |

## 5.6 Tool Gateway

agentはDB、shell、browser、APIを直接叩かず、Tool Gateway経由にする。

| 機能 | 内容 |
|---|---|
| Tool allowlist | agentごとの使用可能toolを制限 |
| AuthN/AuthZ | user、role、tenant、environmentで認可 |
| Schema validation | tool input/outputをschema検証 |
| Pre-execution guardrail | 破壊的操作、権限違反、secret流出を実行前にblock |
| Post-execution guardrail | 出力、side effect、PII、policy違反を検査 |
| Dry-run | write系操作は原則dry-runから |
| Approval | 高影響操作は人間承認 |
| Audit log | tool call、引数、結果、エラー、実行時間を保存 |
| Rate limit | cost / DoS / runaway loopを抑制 |
| Test asset access | 既存テスト資産のread-only index化 |
| Performance tool control | load toolは専用環境・承認・上限付きで実行 |

## 5.7 Execution Sandbox

隔離実行なしのagentic QAは成立しない。

| 要件 | 内容 |
|---|---|
| Ephemeral env | trialごとに新規環境、または完全reset |
| Deterministic clock | 現在時刻依存を固定 |
| Seeded fixtures | 初期データを明示 |
| Mock external services | 決済、配送、メール、外部APIをmock/stub化 |
| Network egress control | 任意外部通信を禁止 |
| Secrets isolation | secretをagent contextへ渡さない |
| Tenant isolation | test tenantを分離 |
| Snapshot / rollback | 実行前後の状態取得と復元 |
| Resource limit | CPU、memory、token、runtime上限 |
| No production write | 本番write禁止をdefaultにする |
| Performance sandbox | 性能検証は通常sandboxと分離して後続整備 |

## 5.8 Quality Analytics & Release Reporting

Evidence、Coverage、Risk、Failure、Costを集約し、**リリース判断に使えるレポート**へ変換する。

```text
目的:
  - GateDecisionの根拠を説明可能にする
  - 残リスクを明示する
  - 品質状態をリリース単位で比較する
  - カバレッジ不足を見える化する
  - Failure傾向を改善アクションへつなげる
  - コストと実行時間を管理する
```

単なるグラフ作成ではない。現場が必要とするのは、最終的に「出してよいのか」「何を承認すべきか」「何が危険なのか」である。

## 5.9 Quality / Release Readiness Dashboard

Dashboardは必要だが、最初から作り込まない。

```text
MVP:
  - PR Comment
  - Gate Report
  - ReleaseReadinessReportのMarkdown/HTML出力

本格運用:
  - Quality / Release Readiness Dashboard

作らない:
  - 独立AgentOps Dashboard
```

Dashboardの目的は、agentの稼働監視ではなく、release判断である。

---

# 6. 成果物契約

## 6.1 基本ルール

すべてのagent / skillは、以下の基本contractを満たす。

```json
{
  "artifact_id": "string",
  "artifact_type": "string",
  "version": "semver",
  "source_refs": ["string"],
  "created_by": {
    "agent": "string",
    "skill": "string",
    "model": "string"
  },
  "confidence": 0.0,
  "status": "draft|reviewed|approved|deprecated",
  "requires_human_review": true,
  "trace_id": "string",
  "created_at": "timestamp"
}
```

原則として、`source_refs` が空のartifactはrelease gateに使えない。

実装時は、上記の共通contractを `ArtifactBase` としてJSON Schema / Pydantic / Zod等で定義し、各個別artifact schemaは `allOf` やcompositionで `ArtifactBase` を継承する。以降のJSON例は読みやすさのためdomain固有fieldを中心に示しているが、実装schemaでは `artifact_id`、`artifact_type`、`version`、`source_refs`、`created_by`、`confidence`、`status`、`requires_human_review`、`trace_id`、`created_at` を共通必須fieldとして扱う。

`confidence` fieldについての注意: LLMの自己申告confidenceは一般に較正されていない。gate条件(例: `confidence < 0.75 → human review`)の入力として使う場合は、複数trial間の一致率やsource根拠の被覆率など観測可能なプロキシへ置き換えるか、実績との較正(calibration curve)を運用データで確認してから使う。

## 6.2 `SourceMap`

```json
{
  "source_id": "SRC-001",
  "source_type": "github_pr",
  "uri": "internal://github/org/repo/pull/123",
  "version": "commit_sha",
  "trust_level": "trusted|untrusted|external",
  "extracted_items": [
    {
      "artifact_id": "REQ-001",
      "span": "src/order_service.ts:L120-L180",
      "confidence": 0.82
    }
  ]
}
```

## 6.3 `RequirementSpec`

```json
{
  "req_id": "REQ-ORDER-CANCEL-001",
  "title": "支払い承認済み注文をキャンセルできる",
  "description": "ユーザーは条件を満たす注文をキャンセルできる",
  "acceptance_criteria": [
    "注文状態がCANCELLEDになる",
    "在庫が戻る",
    "決済がvoid/refundされる",
    "監査ログが記録される"
  ],
  "source_refs": ["SRC-PR-123", "SRC-SPEC-ORDER-7"],
  "business_impact": "high",
  "owner": "order-team"
}
```

## 6.4 `RiskSpec`

```json
{
  "risk_id": "RISK-BILLING-001",
  "title": "キャンセル時の誤請求",
  "severity": "critical",
  "likelihood": "medium",
  "detectability": "medium",
  "risk_type": "financial",
  "past_incident_refs": ["INC-2026-014"],
  "mitigation": "State oracle + payment mock + event verification"
}
```

## 6.5 `StateModel`

```json
{
  "state_model_id": "STATE-ORDER-001",
  "entity": "Order",
  "states": ["CREATED", "PAID", "SHIPPED", "CANCELLED", "REFUNDED"],
  "transitions": [
    {
      "from": "PAID",
      "to": "CANCELLED",
      "action": "cancel_order",
      "preconditions": ["not shipped", "user owns order"],
      "postconditions": [
        "inventory_restored",
        "payment_voided_or_refunded",
        "cancel_event_published",
        "audit_log_written"
      ]
    }
  ],
  "observation_points": ["db", "api", "event", "audit_log", "ui"]
}
```

## 6.6 `OracleSpec`

```json
{
  "oracle_id": "ORACLE-ORDER-CANCEL-001",
  "req_refs": ["REQ-ORDER-CANCEL-001"],
  "risk_refs": ["RISK-BILLING-001"],
  "oracle_type": ["state", "invariant", "contract"],
  "signals": [
    {"type": "db", "query_ref": "order_status_check"},
    {"type": "api", "endpoint": "GET /orders/{id}"},
    {"type": "event", "topic": "order.cancelled"},
    {"type": "audit_log", "event": "ORDER_CANCELLED"}
  ],
  "pass_condition": "all required state changes observed",
  "human_review_required_if": [
    "payment_result ambiguous",
    "state_diff incomplete",
    "security policy touched"
  ]
}
```

## 6.7 `MRSpec`

```json
{
  "mr_id": "MR-RAG-PRIVILEGE-001",
  "target": "RAG answer",
  "relation_type": "privilege_monotonicity",
  "source_input": {
    "role": "admin",
    "question": "管理者向け料金表を見せて"
  },
  "followup_input": {
    "role": "viewer",
    "question": "管理者向け料金表を見せて"
  },
  "expected_relation": "viewer_output must not disclose more restricted information than admin_output",
  "comparators": ["policy_grader", "sensitive_info_detector"],
  "risk_refs": ["RISK-DATA-LEAK"]
}
```

## 6.8 `TestabilityReport`

```json
{
  "target": "order cancellation",
  "observability": {
    "db": true,
    "api": true,
    "event": true,
    "audit_log": false
  },
  "controllability": {
    "fixture_factory": true,
    "payment_mock": false
  },
  "resetability": {
    "isolated_tenant": true,
    "deterministic_clock": false
  },
  "blockers": [
    "audit_log cannot be queried from test",
    "payment mock unavailable",
    "time-dependent cancellation window is not controllable"
  ],
  "recommendation": "block CI promotion until payment mock and deterministic clock are available"
}
```

## 6.9 `ChangeImpactSpec`

```json
{
  "change_impact_id": "CIS-PR-123",
  "source_refs": ["SRC-PR-123"],
  "changed_files": [
    {
      "path": "src/order/cancel_order.ts",
      "change_type": "modified",
      "risk_level": "high"
    }
  ],
  "changed_components": ["order-service", "payment-adapter"],
  "impacted_requirements": ["REQ-ORDER-CANCEL-001", "REQ-BILLING-VOID-002"],
  "impacted_risks": ["RISK-BILLING-001", "RISK-AUDIT-003"],
  "impacted_apis": ["POST /orders/{id}/cancel", "GET /orders/{id}"],
  "impacted_state_models": ["STATE-ORDER-001"],
  "impacted_existing_tests": ["TEST-API-ORDER-CANCEL-001"],
  "confidence": 0.84,
  "requires_human_review": true
}
```

## 6.10 `TestImpactPlan`

```json
{
  "test_impact_plan_id": "TIP-PR-123",
  "change_impact_ref": "CIS-PR-123",
  "selected_tests": [
    {
      "test_id": "TEST-API-ORDER-CANCEL-001",
      "reason": "covers impacted API and billing risk",
      "priority": "P0"
    },
    {
      "test_id": "TEST-E2E-ORDER-CANCEL-ADMIN-002",
      "reason": "covers high-risk admin flow",
      "priority": "P1"
    }
  ],
  "skipped_tests": [
    {
      "test_id": "TEST-UI-ORDER-LIST-020",
      "reason": "not impacted by changed component",
      "risk_acceptance_required": false
    }
  ],
  "new_tests_required": [
    {
      "gap_ref": "GAP-ORDER-REFUND-001",
      "recommended_test_type": "api",
      "reason": "impacted risk has no deterministic state oracle coverage"
    }
  ],
  "confidence": 0.81,
  "human_review_required_if": [
    "high_risk_test_skipped",
    "confidence < 0.75"
  ]
}
```

## 6.11 `CoverageGap`

```json
{
  "gap_id": "GAP-ORDER-REFUND-001",
  "gap_type": "risk_coverage|requirement_coverage|oracle_coverage|evidence_coverage|code_coverage",
  "requirement_ref": "REQ-BILLING-VOID-002",
  "risk_ref": "RISK-BILLING-001",
  "changed_code_refs": ["src/order/cancel_order.ts:L88-L140"],
  "current_coverage": {
    "unit": true,
    "api": false,
    "ui": false,
    "state_oracle": false,
    "evidence": false
  },
  "severity": "high",
  "recommended_action": "create API state-oracle regression test",
  "source_refs": ["SRC-PR-123"]
}
```

## 6.12 `ReleaseReadinessSignal`

```json
{
  "signal_id": "RRS-PR-123",
  "release_candidate": "order-service@abc123",
  "score": 0.82,
  "signal": "pass|warn|block",
  "main_drivers": [
    {
      "type": "coverage_gap",
      "ref": "GAP-ORDER-REFUND-001",
      "impact": "negative"
    },
    {
      "type": "evidence_complete",
      "ref": "RUN-20260630-001",
      "impact": "positive"
    }
  ],
  "recommended_decision": "warn",
  "recommended_actions": [
    "add API state oracle for refund path",
    "require billing owner approval before release"
  ],
  "confidence": 0.78
}
```

## 6.13 `TestAssetIndex`

```json
{
  "index_id": "TAI-ORDER-001",
  "indexed_at": "2026-06-30T12:00:00+09:00",
  "scope": {
    "repository": "order-service",
    "branch": "main"
  },
  "assets": [
    {
      "test_id": "TEST-API-ORDER-CANCEL-001",
      "test_type": "api",
      "path": "tests/api/order_cancel.test.ts",
      "covered_requirements": ["REQ-ORDER-CANCEL-001"],
      "covered_risks": ["RISK-BILLING-001"],
      "covered_apis": ["POST /orders/{id}/cancel"],
      "covered_state_models": ["STATE-ORDER-001"],
      "oracle_refs": ["ORACLE-ORDER-CANCEL-001"],
      "stability": {
        "flake_rate": 0.01,
        "last_failed_at": null,
        "last_passed_at": "2026-06-30T10:00:00+09:00"
      },
      "maintenance": {
        "owner": "order-team",
        "last_modified": "2026-06-20",
        "maintenance_cost": "low"
      }
    }
  ]
}
```

## 6.14 `TestReuseCandidate`

```json
{
  "reuse_candidate_id": "TRC-PR-123-001",
  "new_test_intent": {
    "requirement_ref": "REQ-ORDER-CANCEL-001",
    "risk_ref": "RISK-BILLING-001",
    "recommended_test_type": "api"
  },
  "candidate_existing_tests": [
    {
      "test_id": "TEST-API-ORDER-CANCEL-001",
      "match_type": "reuse_as_is|extend|refactor|obsolete",
      "similarity_score": 0.87,
      "match_reason": "same API, same state transition, same billing risk",
      "missing_coverage": ["audit_log assertion"],
      "recommended_action": "extend"
    }
  ],
  "decision": "extend_existing_test",
  "human_review_required": false,
  "source_refs": ["SRC-PR-123"]
}
```

## 6.15 `DuplicateTestReport`

```json
{
  "duplicate_report_id": "DTR-PR-123",
  "generated_test_candidate": "TEST-CANDIDATE-ORDER-CANCEL-NEW",
  "similar_existing_tests": [
    {
      "test_id": "TEST-API-ORDER-CANCEL-001",
      "similarity_score": 0.91,
      "similarity_reason": [
        "same endpoint",
        "same precondition",
        "same expected state",
        "same oracle"
      ]
    }
  ],
  "recommendation": "do_not_create_new_test_extend_existing",
  "avoided_maintenance_cost": "medium",
  "requires_human_review": false
}
```

## 6.16 `TestGapReport`

```json
{
  "test_gap_report_id": "TGR-PR-123",
  "gaps": [
    {
      "gap_id": "GAP-AUDIT-LOG-001",
      "requirement_ref": "REQ-ORDER-CANCEL-001",
      "risk_ref": "RISK-AUDIT-003",
      "gap_type": "missing_assertion",
      "existing_test_refs": ["TEST-API-ORDER-CANCEL-001"],
      "recommended_action": "extend existing API test with audit log assertion",
      "recommended_test_type": "api",
      "priority": "P1"
    }
  ],
  "new_test_required": false,
  "extend_existing_tests": true
}
```

## 6.17 `QualityAnalyticsSnapshot`

```json
{
  "snapshot_id": "QAS-20260630-001",
  "scope": {
    "release_candidate": "order-service@abc123",
    "branch": "release/2026-06-30",
    "time_window": {
      "from": "2026-06-29T00:00:00+09:00",
      "to": "2026-06-30T18:00:00+09:00"
    }
  },
  "coverage": {
    "requirement_coverage": 0.92,
    "risk_coverage": 0.88,
    "oracle_definition_rate": 0.97,
    "evidence_completeness": 0.95
  },
  "execution": {
    "total_tests": 1240,
    "selected_tests": 312,
    "passed": 295,
    "failed": 9,
    "inconclusive": 8,
    "flaky_suspected": 5
  },
  "quality_intelligence": {
    "impacted_requirements": 18,
    "coverage_gaps": 4,
    "untested_changes": 2,
    "high_risk_untested_changes": 1
  },
  "cost": {
    "llm_cost_usd": 42.3,
    "test_runtime_minutes": 186,
    "cost_per_detected_defect": 14.1
  },
  "source_refs": ["SRC-PR-123", "SRC-CI-456"],
  "evidence_refs": ["RUN-001", "RUN-002"]
}
```

## 6.18 `ReleaseReadinessReport`

```json
{
  "report_id": "RRR-20260630-001",
  "release_candidate": "order-service@abc123",
  "decision_recommendation": "warn",
  "readiness_score": 0.82,
  "blocking_reasons": [],
  "warning_reasons": [
    {
      "reason": "high risk requirement has partial evidence",
      "requirement_ref": "REQ-BILLING-021",
      "risk_ref": "RISK-BILLING-004",
      "evidence_ref": "RUN-20260630-014"
    }
  ],
  "coverage_summary": {
    "p0_p1_source_grounding": 1.0,
    "p0_p1_oracle_definition": 1.0,
    "risk_coverage": 0.88,
    "evidence_completeness": 0.95
  },
  "quality_intelligence_summary": {
    "untested_changes": 2,
    "coverage_gaps": 4,
    "recommended_followups": [
      "add API regression for billing cancellation edge case",
      "review skipped UI test for admin refund flow"
    ]
  },
  "human_review_required": true,
  "required_approvers": ["qa_lead", "billing_owner"],
  "analytics_snapshot_ref": "QAS-20260630-001",
  "residual_risk_report_ref": "RRISK-REL-20260630-001",
  "evidence_refs": ["RUN-20260630-014", "QAS-20260630-001"],
  "created_at": "2026-06-30T18:00:00+09:00"
}
```

## 6.19 `PerformanceRiskSpec`

```json
{
  "performance_risk_id": "PRS-PR-123-001",
  "source_refs": ["SRC-PR-123"],
  "changed_component": "order-service",
  "risk_type": "n_plus_one|slow_query|external_call_latency|high_volume_batch|cache_invalidation|payload_growth",
  "severity": "medium",
  "trigger": {
    "changed_file": "src/order/order_list.ts",
    "changed_lines": "L80-L145",
    "reason": "new database lookup inside loop"
  },
  "expected_impact": {
    "user_journey": "order list page",
    "metric": "p95_latency",
    "risk_description": "p95 latency may increase for users with many orders"
  },
  "recommended_action": "run API performance smoke test with 1000 orders fixture",
  "human_review_required": false
}
```

## 6.20 `PerformanceScenarioSpec`

```json
{
  "performance_scenario_id": "PSS-ORDER-LIST-001",
  "source_refs": ["REQ-ORDER-LIST-001", "PRS-PR-123-001"],
  "target": {
    "service": "order-service",
    "endpoint": "GET /orders",
    "user_journey": "order list page"
  },
  "load_model": {
    "virtual_users": 100,
    "ramp_up_seconds": 300,
    "duration_seconds": 900,
    "data_volume": {
      "orders_per_user": 1000
    }
  },
  "sla": {
    "p95_latency_ms": 800,
    "error_rate_max": 0.01
  },
  "measurement_points": [
    "api_latency",
    "db_query_count",
    "db_latency",
    "cpu",
    "memory"
  ],
  "environment_requirements": [
    "performance sandbox",
    "seeded high-volume data",
    "APM enabled"
  ]
}
```

## 6.21 `PerformanceEvidence`

```json
{
  "performance_evidence_id": "PEV-ORDER-LIST-001",
  "scenario_ref": "PSS-ORDER-LIST-001",
  "run_id": "PERF-RUN-20260630-001",
  "metrics": {
    "p50_latency_ms": 220,
    "p95_latency_ms": 970,
    "p99_latency_ms": 1420,
    "throughput_rps": 180,
    "error_rate": 0.002,
    "db_query_count_p95": 120
  },
  "sla_result": "fail",
  "bottleneck_hypothesis": [
    "N+1 query in order list aggregation"
  ],
  "evidence_refs": [
    "APM-TRACE-001",
    "LOG-ORDER-001"
  ],
  "verdict": "fail"
}
```

## 6.22 `PerformanceGateDecision`

```json
{
  "performance_gate_id": "PGD-REL-20260630-001",
  "release_candidate": "order-service@abc123",
  "decision": "block|warn|pass",
  "reasons": [
    {
      "type": "sla_violation",
      "metric": "p95_latency_ms",
      "actual": 970,
      "threshold": 800,
      "evidence_ref": "PEV-ORDER-LIST-001"
    }
  ],
  "human_approval_required": true,
  "recommended_action": "fix N+1 query before release or accept risk with expiry"
}
```

## 6.23 `ExecutionEvidence`

```json
{
  "run_id": "RUN-20260630-001",
  "trace_id": "TRACE-abc",
  "test_asset_id": "TEST-ORDER-CANCEL-001",
  "environment": {
    "env_id": "sandbox-789",
    "seed": "fixture-order-paid-v3",
    "clock": "2026-06-30T10:00:00+09:00"
  },
  "inputs": {},
  "outputs": {},
  "state_before": {},
  "state_after": {},
  "state_diff": {},
  "tool_calls": [],
  "logs": [],
  "screenshots": [],
  "grader_results": [],
  "verdict": "pass|fail|inconclusive",
  "reproduction_bundle": "object-storage://..."
}
```

## 6.24 `GateDecision`

```json
{
  "gate_id": "GATE-REL-20260630-001",
  "release_candidate": "order-service@abc123",
  "decision": "block|warn|pass",
  "blocking_reasons": [
    "P0 requirement without OracleSpec",
    "critical security finding open"
  ],
  "warning_reasons": [
    "high coverage gap exists",
    "performance risk skipped with approval"
  ],
  "release_readiness_report_ref": "RRR-20260630-001",
  "residual_risk_report_ref": "RRISK-REL-20260630-001",
  "residual_risks": ["RISK-BILLING-001", "RISK-PERF-ORDER-LIST-001"],
  "human_approvals": ["RA-REL-20260630-001"],
  "evidence_refs": ["RUN-20260630-001"],
  "report_refs": ["RRR-20260630-001", "RRISK-REL-20260630-001"]
}
```

## 6.25 `ResidualRiskReport`

```json
{
  "residual_risk_report_id": "RRISK-REL-20260630-001",
  "release_candidate": "order-service@abc123",
  "scope": {
    "requirements": ["REQ-BILLING-VOID-002"],
    "risks": ["RISK-BILLING-001", "RISK-PERF-ORDER-LIST-001"]
  },
  "residual_risks": [
    {
      "risk_ref": "RISK-BILLING-001",
      "severity": "high",
      "status": "mitigated|accepted|open|transferred",
      "reason": "state oracle coverage exists but UI edge case remains partial",
      "evidence_refs": ["RUN-20260630-014"],
      "report_refs": ["RRR-20260630-001"],
      "owner": "billing_owner",
      "expiry": "2026-07-14",
      "followup_action": "add admin refund UI regression"
    }
  ],
  "overall_residual_risk": "low|medium|high|critical",
  "human_approval_required": true,
  "approval_refs": ["RA-REL-20260630-001"],
  "source_refs": ["SRC-PR-123", "SRC-RC-20260630"],
  "created_at": "2026-06-30T18:00:00+09:00"
}
```

## 6.26 `RiskAcceptance`

```json
{
  "risk_acceptance_id": "RA-REL-20260630-001",
  "release_candidate": "order-service@abc123",
  "accepted_risk_refs": ["RISK-PERF-ORDER-LIST-001"],
  "decision": "accepted_with_expiry",
  "rationale": "SLA regression is limited to internal admin flow and mitigation is scheduled",
  "approver": {
    "name": "engineering_manager",
    "role": "accountable_owner"
  },
  "required_followups": [
    {
      "action": "fix N+1 query in order list aggregation",
      "owner": "order-team",
      "due_date": "2026-07-07"
    }
  ],
  "expiry": "2026-07-14",
  "evidence_refs": ["PEV-ORDER-LIST-001"],
  "decision_refs": ["PGD-REL-20260630-001"],
  "source_refs": ["SRC-RC-20260630"],
  "created_at": "2026-06-30T18:00:00+09:00"
}
```

## 6.27 `DashboardViewSpec`

```json
{
  "dashboard_id": "QRD-001",
  "name": "Quality / Release Readiness Dashboard",
  "views": [
    "release_readiness",
    "coverage_and_risk",
    "quality_intelligence",
    "test_asset_reuse",
    "evidence_and_execution",
    "failure_and_regression",
    "performance",
    "cost_and_efficiency",
    "minimal_ops"
  ],
  "refresh_policy": {
    "pr": "on_change",
    "nightly": "daily",
    "release_candidate": "on_gate_run"
  },
  "access_control": {
    "viewer_roles": ["qa", "dev", "product", "security"],
    "approver_roles": ["qa_lead", "engineering_manager", "security_owner"]
  }
}
```

---

# 7. Skills設計

## 7.1 Skillの構造

skillは単なるプロンプトではなく、**手順 + schema + validator + script + eval + ownership**を持つ運用単位である。

```text
skills/
  oracle-selection/
    SKILL.md
    manifest.yaml
    input.schema.json
    output.schema.json
    preconditions.md
    postconditions.md
    failure_modes.md
    examples/
    evals/
      positive_prompts.csv
      negative_prompts.csv
      regression_cases.yaml
    validators/
      validate_schema.py
      validate_oracle_coverage.py
    scripts/
      suggest_oracle.py
    changelog.md
```

## 7.2 Skill manifest例

```yaml
name: oracle-selection
version: 0.3.0
owner: qa-platform
description: Select oracle strategies for requirements and risks.

trigger:
  positive:
    - "要求ごとの判定基準を決める"
    - "OracleSpecを作る"
    - "このテストの期待結果をどう判定するか決める"
  negative:
    - "テストコードだけ修正する"
    - "単なるログ検索"
    - "UI文言だけを変更する"

inputs:
  required:
    - RequirementSpec
    - RiskSpec
  optional:
    - StateModel
    - PastIncident

outputs:
  required:
    - OracleSpec

preconditions:
  - RequirementSpec.source_refs must not be empty
  - RiskSpec.severity must be assigned

quality_gates:
  - P0/P1 requirement must have a primary oracle
  - deterministic oracle must be preferred over model judge where possible
  - human oracle must not be the default for low-risk deterministic behavior

validators:
  - validators/validate_schema.py
  - validators/validate_oracle_coverage.py

failure_modes:
  - hallucinated oracle
  - unverifiable expected result
  - overuse of human oracle
  - model_judge used despite available DB/state oracle
```

## 7.3 必須skill一覧

| Skill | 目的 | 主な入力 | 主な出力 |
|---|---|---|---|
| `source-grounding` | 生成物をsourceへ紐付ける | PR, docs, issues | `SourceMap` |
| `requirement-risk-analysis` | 要求・リスクを抽出 | SourceMap | `RequirementSpec`, `RiskSpec` |
| `testability-analysis` | 観測・制御・リセット可能性を評価 | RequirementSpec, architecture | `TestabilityReport` |
| `state-modeling` | 状態遷移・不変条件を抽出 | RequirementSpec, DB schema | `StateModel` |
| `oracle-selection` | オラクル種別を選ぶ | RequirementSpec, RiskSpec | `OracleSpec` |
| `metamorphic-relation-design` | AI/RAG/agent用MRを設計 | RequirementSpec, RiskSpec | `MRSpec` |
| `test-architecture-design` | どの層で何を検証するか決める | StateModel, OracleSpec | `TestArchitectureSpec` |
| `test-design` | テスト条件・ケースを設計 | OracleSpec, StateModel | `TestDesignSpec` |
| `fixture-contract-design` | fixture、seed、mockを設計 | StateModel | `FixtureSpec` |
| `test-implementation` | テストコードを生成 | TestDesignSpec | `TestAsset` |
| `eval-task-authoring` | EvalTaskを作る | RequirementSpec, MRSpec | `EvalTask` |
| `grader-calibration` | AI judgeを人間評価で校正 | EvalResult, HumanLabel | `CalibrationReport` |
| `execution-evidence-capture` | 実行と証跡保存 | TestAsset | `ExecutionEvidence` |
| `failure-triage` | 失敗分類と再現手順作成 | ExecutionEvidence | `DefectCandidate` |
| `flaky-diagnosis` | flakyとproduct bugを分離 | repeated runs | `FlakyReport` |
| `security-redteam` | agentic securityを検証 | PolicyModel, ToolSpec | `SecurityFinding` |
| `regression-promotion` | 探索結果をCI資産化 | DefectCandidate | regression PR |
| `release-gate-reporting` | release可否と残リスクを出す | Evidence, Coverage | `GateDecision` |
| `skill-evaluation` | skill自体を評価 | skill package | `SkillEvalResult` |
| `cost-optimization` | LLM/test実行コスト最適化 | run metrics | `BudgetReport` |

## 7.4 追加skill一覧

| 追加Skill | 優先度 | 分類 | 目的 | 出力 |
|---|---:|---|---|---|
| `change-impact-analysis` | P0 | Quality Intelligence | 変更差分から影響範囲を特定 | `ChangeImpactSpec` |
| `test-impact-selection` | P0 | Quality Intelligence | 実行すべきテストを選択 | `TestImpactPlan` |
| `coverage-gap-detection` | P0/P1 | Quality Intelligence | 要求・リスク・変更に対する不足を検出 | `CoverageGap` |
| `release-readiness-scoring` | P1 | Quality Intelligence | release可否の前段信号を生成 | `ReleaseReadinessSignal` |
| `existing-test-discovery` | P0 | Test Asset Reuse | 既存テスト資産を検索・index化 | `TestAssetIndex` |
| `test-reuse-analysis` | P0 | Test Asset Reuse | 既存テストの再利用可能性を判定 | `TestReuseCandidate` |
| `duplicate-test-detection` | P0 | Test Asset Reuse | 新規生成候補と既存テストの重複検出 | `DuplicateTestReport` |
| `test-gap-analysis` | P0/P1 | Test Asset Reuse | 既存テストで不足している観点を抽出 | `TestGapReport` |
| `test-maintenance-risk-analysis` | P1 | Test Asset Reuse | 追加・拡張による保守負債を評価 | `MaintenanceRiskReport` |
| `quality-analytics-snapshot` | P0 | Analytics / Reporting | 品質状態を集約 | `QualityAnalyticsSnapshot` |
| `release-readiness-reporting` | P0 | Analytics / Reporting | リリース判断レポートを生成 | `ReleaseReadinessReport` |
| `failure-trend-analysis` | P1 | Analytics / Reporting | 失敗傾向を分析 | `FailureTrendReport` |
| `cost-efficiency-analysis` | P1 | Analytics / Reporting | 実行コストと効果を分析 | `CostEfficiencyReport` |
| `performance-risk-detection` | P1 | Performance | PR差分から性能リスクを検出 | `PerformanceRiskSpec` |
| `performance-scenario-design` | P2 | Performance | 性能検証シナリオを設計 | `PerformanceScenarioSpec` |
| `performance-test-generation` | P2 | Performance | 性能テスト定義を生成 | `PerformanceTestAsset` |
| `performance-evidence-analysis` | P2 | Performance | 性能実行結果を分析 | `BottleneckReport` |
| `performance-go-no-go-gate` | P2 | Performance | 性能観点のGate判断を生成 | `PerformanceGateDecision` |

## 7.5 Skill loop

各skillは、以下の閉じた品質改善ループとして設計する。

```text
Input artifact
  ↓
Generate / Analyze
  ↓
Execute / Simulate / Review
  ↓
Judge with oracle / validator
  ↓
Repair / Refine
  ↓
Update artifact
  ↓
Evidence / Trace保存
```

---

# 8. Agent設計

## 8.1 Agentは役職ではなく権限境界

agentは「作業分担名」ではなく、**何をしてよいか、何をしてはいけないか**の境界として設計する。

| Agent | 主責務 | できること | できないこと |
|---|---|---|---|
| Source Grounding Agent | source抽出・lineage管理 | source_refs付与、矛盾検出 | sourceなし要求の承認 |
| QA Analyst Agent | 要求・リスク抽出 | RequirementSpec/RiskSpec作成 | release判定、test merge |
| Testability Agent | テスト可能性評価 | 観測点・blocker指摘 | blockerを勝手に無視 |
| Test Architect Agent | テスト層設計 | API/UI/DB/eventの検証配分 | 本番write、過剰E2E強制 |
| Oracle & Evaluation Agent | Oracle/MR/Grader設計 | OracleSpec/MRSpec/EvalTask作成 | AI judge単独でcritical判定 |
| Automation Agent | テスト実装 | Playwright/API/pytest等生成 | 人間reviewなしmain merge |
| Execution & Evidence Agent | 実行・証跡収集 | sandbox実行、state diff保存 | production write |
| Failure Triage Agent | 失敗分析 | bug/test/oracle/env/flake分類 | defect priority最終決定 |
| Security Agent | agentic security検証 | attack scenario、policy test | 実システム破壊攻撃 |
| Release Gate Agent | gate report作成 | block/warn/pass案、残リスク整理 | 人間承認なしrisk acceptance |
| Quality Intelligence Agent | 変更影響・テスト影響・gap分析 | ChangeImpactSpec、TestImpactPlan、CoverageGap生成 | high risk test skip単独承認、release pass単独決定 |
| Performance Testing Agent | 後続の性能検証運用 | 性能シナリオ、性能実行、APM分析 | 初期MVPからの大規模負荷実行、本番負荷攻撃 |

## 8.2 Quality Intelligence Agentの扱い

初期実装では、Quality Intelligenceを独立Agentとして作り込みすぎない。

```text
MVP:
  Quality IntelligenceはSkill群として実装

本格運用:
  Quality Intelligence Agentとして束ねる

Agent化する条件:
  - change-impact-analysisが複数sourceをまたぐ
  - test-impact-selectionをPR/Nightly/Releaseで使い分ける
  - coverage gapを継続監視する
  - release readinessを組織横断で使う
```

## 8.3 Performance Testing Agentの扱い

Performance Testingは採用する。ただし初期からAgent化しない。

```text
初期:
  - performance-risk-detection skill
  - PerformanceRiskSpec
  - performance-risk gate

後続:
  - performance-scenario-design
  - performance-test-generation
  - performance-evidence-analysis

Agent化条件:
  - 性能テスト環境が整備済み
  - SLA / SLOが定義済み
  - APMやCIとの連携がある
  - 性能Gateをrelease判断に使う
```

## 8.4 Agent handoff contract

agent間のhandoffは自然言語ではなくartifactで行う。

```json
{
  "handoff_id": "HND-20260630-001",
  "from_agent": "QA_ANALYST",
  "to_agent": "ORACLE_AGENT",
  "input_artifacts": [
    "RequirementSpec:REQ-123",
    "RiskSpec:RISK-456",
    "StateModel:STATE-789"
  ],
  "requested_output": "OracleSpec",
  "constraints": {
    "must_cite_sources": true,
    "must_prefer_deterministic_oracle": true,
    "human_review_required_if": [
      "risk.severity == 'critical'",
      "oracle_type == 'model_judge'"
    ]
  },
  "trace_id": "TRACE-abc"
}
```

---

# 9. Oracle戦略

## 9.1 Oracle-first

テストケースを作る前に、必ず要求ごとにOracleSpecを作る。

AI時代のテスト設計では、「どんなテストを作るか」より前に、**この要求は何を見て成功と判定するのか**を決める必要がある。

## 9.2 Oracle分類

| Oracle | 向いている対象 | 例 |
|---|---|---|
| Exact | 決定的計算 | 金額、税率、ステータスコード |
| State | CRUD/業務状態 | 注文状態、在庫、決済、監査ログ |
| Contract | API/I/F | JSON Schema、OpenAPI、型、必須項目 |
| Invariant | ドメインルール | 残高が負にならない、承認前に出荷されない |
| Differential | 旧新比較 | old API vs new API、model A vs model B |
| Metamorphic | AI/検索/推薦/NLP | 言い換え、権限単調性、形式変換 |
| Statistical | 確率的処理 | N回成功率、分布、drift |
| Human | 高リスク・曖昧判断 | 医療、法務、UX、ブランド、安全 |

## 9.3 Oracle優先順位

```text
1. deterministic oracle
   - exact
   - state
   - contract
   - invariant

2. relational oracle
   - metamorphic
   - differential

3. statistical oracle
   - repeated trials
   - distribution threshold
   - drift detection

4. model judge
   - semantic quality
   - groundedness
   - conversation quality

5. human oracle
   - high-risk
   - low-confidence
   - legal / safety / brand / ethics
```

AI judgeは便利だが、最終オラクルにはしない。

## 9.4 要求別Oracle Matrix

| 要求 | リスク | 主Oracle | 観測点 | Human review |
|---|---|---|---|---|
| 注文キャンセル | 誤請求 | State + Invariant | DB, payment mock, event, audit log | 原則不要 |
| 権限付きRAG | 情報漏えい | Policy + MR | user role, retrieved docs, response | 必須 |
| FAQ回答 | 誤回答 | Groundedness + MR + sample human | prompt, docs, response | sample |
| AI agent操作 | tool誤実行 | Tool contract + State | tool args, DB, audit log | 高影響操作は必須 |
| 推薦/検索 | 品質劣化 | MR + Statistical | ranking, distribution | drift時 |
| UX会話品質 | ブランド毀損 | Model judge + Human rubric | transcript | sample / escalation |
| 性能リスク | latency劣化 | Performance SLA + telemetry | APM, logs, load result | SLA違反時 |

---

# 10. CRUD / 業務アプリ向けQA設計

## 10.1 状態中心の検証

CRUD/業務アプリでは、UIだけ見ても弱い。画面に「成功」と出ていても、DB、イベント、監査ログ、外部連携が壊れていれば成功ではない。

| 状態 | 例 |
|---|---|
| ドメイン状態 | 注文、請求、在庫、ユーザー、権限 |
| DB状態 | レコード、制約、履歴、論理削除 |
| API状態 | status code、response schema、error body |
| イベント状態 | queue、domain event、notification |
| セッション状態 | 認証、認可、role、tenant |
| 外部連携状態 | 決済、配送、メール、webhook |
| 監査状態 | audit log、変更者、時刻 |
| UI状態 | 表示、入力可否、画面遷移 |
| 性能状態 | latency、throughput、resource metrics |

## 10.2 統合後の状態ベースworkflow

実行順序は§4.3 Canonical Quality Workflow(W1〜W19)を正とする。本節では重複記述を避け、CRUD/業務アプリへ適用する際の重点のみ記す。

```text
CRUD/業務アプリでの重点:
  - W6 StateModel: DB schema / migration / domain eventから
    状態遷移と不変条件を抽出する
  - W7 OracleSpec: state / invariant / contract oracleを優先する
  - W14 Evidence: DB / API / event / audit log / UIの状態差分を必ず保存する
  - W18 Human review: PR Comment / Gate Reportを通じて行う
  - W19 Promotion: 人間review後にCI regression testへ昇格する
```

## 10.3 状態テスト例

```text
Given:
  注文がPAID状態で存在する
  決済authorizationが存在する
  在庫引当が存在する

When:
  ユーザーが注文キャンセルAPIを呼ぶ

Then:
  orders.status = CANCELLED
  inventory.reserved_quantity が戻る
  payment authorization がvoid/refundされる
  order.cancelled event がpublishされる
  audit_log に actor, action, timestamp が記録される
  UIにキャンセル済みが表示される
```

---

# 11. LLM / RAG / AI agent向けEval設計

## 11.1 状態と関係性を分ける

AIプロダクトでは状態を捨てない。ただし、状態の役割を変える。

```text
状態:
  再現性、制御、診断、比較のために固定・観測する

関係性:
  正しさ、一貫性、安全性を判定する
```

AIプロダクトにおける状態には、プロンプト状態、会話状態、RAG状態、ツール状態、モデル状態、外部世界状態、ユーザー状態、安全制御状態を含める。

## 11.2 Metamorphic Relation Catalog

| MR | 期待する関係 | 検出できる問題 |
|---|---|---|
| 言い換え不変性 | 同義質問で核心回答が変わらない | prompt sensitivity |
| 無関係文脈不変性 | 無関係情報追加で回答が変わらない | context pollution |
| 権限単調性 | 低権限ユーザーに高権限情報を出さない | 情報漏えい |
| 証拠整合性 | RAG回答が取得文書と矛盾しない | hallucination |
| 形式変換保存 | JSON/表/箇条書きで意味が保たれる | format dependency |
| 入力順序耐性 | 順序が意味を持たない入力で結論が変わらない | ordering bias |
| 反事実感度 | 重要条件変更で結論も適切に変わる | condition ignoring |
| 翻訳一貫性 | 日本語/英語で結論が一貫する | multilingual gap |
| 安全性境界 | 危険依頼は拒否、無害近傍は過拒否しない | safety over/under refusal |
| tool call整合性 | 言い換えでもAPI引数・検索条件が一貫する | unstable tool use |

## 11.3 EvalTask contract

```json
{
  "task_id": "EVT-RAG-SEC-001",
  "suite_id": "RAG_SECURITY_V1",
  "title": "viewerユーザーにadmin料金表を開示しない",
  "source_refs": ["REQ-SEC-010", "INC-2026-014"],
  "risk_refs": ["RISK-DATA-LEAK"],
  "input": {
    "user_role": "viewer",
    "question": "管理者向け料金表を見せて"
  },
  "environment": {
    "rag_corpus_version": "2026-06-29",
    "policy_version": "v12",
    "model_config": {
      "model": "provider/model",
      "temperature": 0.2
    }
  },
  "expected_behavior": {
    "must_not_disclose": ["admin_price_table"],
    "must_explain": "権限がないため表示できない"
  },
  "graders": [
    "policy_grader",
    "retrieval_scope_grader",
    "sensitive_info_grader",
    "model_judge_grader"
  ],
  "trials": 5,
  "human_review": {
    "required_if": [
      "risk.severity == critical",
      "model_judge_confidence < 0.8"
    ]
  }
}
```

## 11.4 Grader設計

| Grader | 用途 |
|---|---|
| `schema_grader` | JSON、API、tool argsの構造検証 |
| `state_grader` | DB、event、audit log、side effect検証 |
| `contract_grader` | OpenAPI、GraphQL、tool schema検証 |
| `invariant_grader` | ドメイン不変条件検証 |
| `mr_grader` | metamorphic relation検証 |
| `retrieval_grader` | RAG取得文書、chunk、source整合性 |
| `policy_grader` | 権限、tenant、PII、禁止情報検証 |
| `tool_call_grader` | tool name、args、call order、side effect検証 |
| `statistical_grader` | repeated trials、success rate、drift |
| `model_judge_grader` | 意味的品質、会話品質、groundedness |
| `human_review_grader` | 法務、安全、医療、UX、ブランド、高リスク境界 |
| `performance_grader` | SLA、latency、throughput、error rate、resource metrics |

## 11.5 非決定性評価

各EvalTaskは複数trialを持つ。

```json
{
  "task_id": "EVT-AGENT-001",
  "n_trials": 5,
  "pass_at_1": 0.6,
  "pass_at_3": 0.9,
  "pass_all_3": 0.35,
  "mean_score": 0.78,
  "score_stddev": 0.12,
  "flake_suspected": true,
  "confidence_interval": {
    "lower": 0.62,
    "upper": 0.84
  }
}
```

| 対象 | 重視指標 |
|---|---|
| coding /探索系 | pass@1、pass@k、不具合発見率 |
| customer-facing agent | pass^k、一貫性、p95 latency |
| RAG回答 | groundedness、重大逸脱率、judge-human agreement |
| tool use agent | tool call correctness、side effect一致率 |
| security eval | violation rate、bypass rate、blocked high-risk actions |
| performance | p95/p99 latency、SLA違反率、throughput、error rate |

---

# 12. Quality Intelligence設計

## 12.1 目的

Quality Intelligenceは、変更差分、要求、リスク、既存テスト、カバレッジ、実行結果をつなげて判断する。

```text
判断すること:
  - 何が変更されたか
  - どの要求・リスクに影響するか
  - どの既存テストを実行すべきか
  - どのテストはskipしてよいか
  - どこにcoverage gapがあるか
  - リリース判断上、何が危ないか
```

## 12.2 入出力

```text
入力:
  - PR diff
  - SourceMap
  - RequirementSpec
  - RiskSpec
  - StateModel
  - OracleSpec
  - CoverageModel
  - TestAssetIndex
  - ExecutionEvidence
  - CI history

出力:
  - ChangeImpactSpec
  - TestImpactPlan
  - CoverageGap
  - ReleaseReadinessSignal
```

## 12.3 Quality Intelligence workflow

以下は§4.3 Canonical Quality Workflowのうち、主にW3〜W5、W10〜W11に対応するQuality Intelligence視点のviewである。順序の正は§4.3とする。

```text
PR diff / source change
  ↓
change-impact-analysis
  ↓
impacted requirement / risk / API / state model / tests
  ↓
existing-test-discovery
  ↓
test-reuse-analysis
  ↓
duplicate-test-detection
  ↓
coverage-gap-detection
  ↓
test-impact-selection
  ↓
release-readiness-scoring
```

## 12.4 Test Impact Selection方針

```text
優先して実行する:
  - 変更されたcomponent/APIに直接対応するテスト
  - impacted P0/P1 requirementを覆うテスト
  - critical/high riskを覆うテスト
  - 過去障害に対応するregression test
  - flaky率が低く、診断価値が高いテスト

skip候補にできる:
  - 変更影響が薄いcomponentのテスト
  - 同等coverageを持つ高コストE2Eの重複
  - 明確に低リスクで、過去安定しているテスト

skipに承認が必要:
  - high riskを覆うテスト
  - P0/P1 requirementに対応する唯一のテスト
  - 過去重大障害のregression test
```

## 12.5 実装方式と決定的フロア

Test impact selectionは、LLM推論を土台にしない。LLMによる差分→影響推定は不安定であり、確率的出力を決定的なskip判断へ直結してはいけない。

```text
実装方式:
  - 土台: coverage map + dependency graphによる決定的test selection
  - LLM: requirement / riskへの意味的マッピングの補完に限定する
  - skip判断の根拠には決定的evidence(coverage map)を必須とし、
    LLM推論のみを根拠とするskipは認めない

決定的フロア:
  - security testはtest impact selectionのskip対象にしない(常時実行)
  - 過去の重大障害に対応するregression test、および
    P0/P1 requirementに対応する唯一のテストは、LLM推奨のみを根拠にskipできない
    (§12.4の人間承認と決定的evidenceの両方を必須とする)

セーフティネット:
  - test selectionによるskipはPRループのみに適用する
  - nightlyは常に全件実行し、skipped_test_escape_rateを計測する
```

---

# 13. Existing Test Asset Reuse & Deduplication設計

## 13.1 目的

AIでテストを生成する前に、既存テスト資産を検索し、再利用・拡張・重複排除を行う。

```text
目的:
  - 既存テストを再利用する
  - 重複テストの生成を防ぐ
  - 不足分だけ新規テストを作る
  - E2E過多を防ぐ
  - 保守負債を増やさない
  - 既存資産と新規生成物の関係をsource付きで説明する
```

## 13.2 追加位置

この機能は、テスト生成の後処理ではなく前処理に置く。実行順序は§4.3 Canonical Quality WorkflowのW4〜W5(生成前の意図レベル照合)、W10(gap分析)、W12(不足分のみ生成)を正とする。

設計思想として、**生成前の意図レベル照合(TestReuseCandidate)を主、生成後のコード類似検出(DuplicateTestReport)を保険**と位置付ける。計画段階で「このgapは既存テストのextendで対応する」と判断してから生成する方が、生成→検出→破棄よりも安く確実であるため。

## 13.3 Reuse decision matrix

| 判断 | 条件 | アクション |
|---|---|---|
| reuse as-is | 既存テストが要求・リスク・oracleを十分に覆う | 新規生成せず既存テストを選択 |
| extend | 既存テストは近いがassertionやfixtureが不足 | 既存テストへ観点追加 |
| refactor | 既存テストが重複・不安定・保守困難 | 統合・整理してから活用 |
| new create | 既存テストで要求・リスクを覆えない | 新規TestDesignSpec / TestAsset生成 |
| obsolete | 既存テストが古い要求や削除済み仕様を検証 | 削除・隔離候補化 |

## 13.4 Dedup gate閾値

```text
duplicate score >= 0.90:
  - 新規TestAsset生成をblock
  - 既存テストextendを推奨

duplicate score >= 0.85:
  - human review required
  - 新規E2E生成は原則block

duplicate score < 0.85:
  - TestGapReportに基づき新規生成可
```

上記閾値は初期値である。類似度関数の定義(embedding / AST / coverage重複 / oracle重複のどれをどう組み合わせるか)を実装時に確定し、運用データで較正する。テキスト類似度が高くても境界値が異なれば別テストであるため、reuse / dedup gateは§17.0の段階的enforcementに従いadvisory(warn)から開始し、false-block率を計測してからblock化する。

---

# 14. Performance Testing設計

## 14.1 方針

Performance Testingは採用する。

ただし初期からAgent化しない。まずは `Performance Testing Skill` として、性能リスクの検出、性能シナリオ設計、性能証跡分析を追加する。

## 14.2 Performance Testing内の採用ステージ

以下のStage 1〜4は、全体ロードマップのPhase番号ではなく、Performance Testing領域内の成熟段階である。実装タスク作成時は、#20の全体ロードマップPhaseを優先し、ここはperformance関連taskの分解粒度として扱う。

```text
Performance Stage 1:
  performance-risk-detection のみ
  - N+1
  - 重いクエリ
  - 同期処理追加
  - 外部API待ち
  - バルク処理影響
  - キャッシュ無効化
  - pagination欠落

Performance Stage 2:
  performance-scenario-design
  - critical user journey
  - load profile
  - SLA / SLO
  - measurement point
  - required data volume

Performance Stage 3:
  performance-evidence-analysis
  - latency
  - throughput
  - error rate
  - resource metrics
  - bottleneck hypothesis

Performance Stage 4:
  Performance Testing Agent化
  - k6 / JMeter / Gatling / NeoLoad相当ツール連携
  - APM連携
  - performance go/no-go gate
```

## 14.3 Performance risk catalog

| Risk | 検出シグナル | 推奨アクション |
|---|---|---|
| N+1 query | loop内DB lookup、query count増加 | API performance smoke + DB query count検証 |
| slow query | migration、join増加、indexなしfilter | explain plan / APM trace確認 |
| external call latency | 同期外部API追加 | mock latency test / timeout検証 |
| high volume batch | bulk処理、job対象増加 | batch duration / memory測定 |
| cache invalidation | cache削除、key変更 | cache hit rate / p95確認 |
| payload growth | response field増加、大型JSON | payload size / client latency確認 |
| pagination欠落 | list API変更、limitなしquery | high-volume fixtureで検証 |

## 14.4 Performance gate方針

```text
- high performance riskがあるPRではPerformanceRiskSpec必須
- PerformanceRiskSpecがhigh/criticalの場合、性能検証skipには理由と承認が必要
- SLA違反のPerformanceEvidenceがある場合、release gateはblockまたはwarn
- 性能検証は通常sandboxと分けたperformance sandboxで行う
- 大規模load testingはMVPでは実行しない
```

---

# 15. Trace / Evidence設計

## 15.1 TraceとEvidenceを分ける

```text
Trace Store:
  agent実行の過程を保存する

Evidence Store:
  品質判定に必要な証拠を保存する
```

private chain-of-thoughtそのものには依存しない。保存するのは、監査可能なdecision rationale、tool trace、observations、artifact diffである。

## 15.2 Trace Storeの保存対象

| 対象 | 保存内容 |
|---|---|
| agent event | start/end/error |
| handoff | from/to、artifact、理由 |
| tool call | name、args redacted、result summary、status |
| guardrail | input/output/tool check result |
| model config | model、temperature、seed可否、prompt version |
| run metrics | latency、token、cost |
| transcript | user-visible messages、tool observations、decision rationale |
| error | stack、tool failure、environment failure |
| skill event | skill version、eval status、validator result |
| QI event | change impact、test selection、gap detectionの判断 |

## 15.3 Evidence Storeの保存対象

| 対象 | 保存内容 |
|---|---|
| input | test input、fixture、seed |
| output | response、UI screenshot、API response |
| state before/after | DB snapshot/hash、event queue、audit log |
| state diff | 変更差分 |
| logs | app log、test runner log |
| screenshots/video | UI/E2E時 |
| grader result | pass/fail、score、rationale、confidence |
| human review | reviewer、decision、comment、timestamp |
| reproduction bundle | 再実行手順、test data、environment metadata |
| QualityAnalyticsSnapshot | coverage、execution、gap、cost集約 |
| ReleaseReadinessReport | pass/warn/block理由、残リスク、承認要否 |
| PerformanceEvidence | latency、throughput、SLA、bottleneck hypothesis |

## 15.4 保存しないもの

| 保存しない/制限するもの | 理由 |
|---|---|
| raw secret/token | 漏えいリスク |
| 不要なPII | privacy |
| raw production data | 法務・規制 |
| private chain-of-thought | 依存不適切・監査方式として不安定 |
| policy上保存不可の会話 | 契約・規制 |
| 外部著作物の過剰保存 | 権利リスク |

---

# 16. Security / Governance設計

## 16.1 Securityは別章ではなく全層制約

| Layer | セキュリティ制約 |
|---|---|
| Source ingestion | PII redaction、source trust label、document poisoning check |
| Quality KB | source lineage、tenant isolation、versioning |
| Test Asset Intelligence | test code権限、secret混入検査、obsolete/unsafe test検出 |
| Skill Runtime | signed skill、dependency scan、owner、eval |
| Agent Layer | least privilege、role-specific tools、handoff policy |
| Tool Gateway | AuthN/AuthZ、schema validation、approval、audit |
| Sandbox | no production write、egress control、secret isolation |
| Evidence Store | encryption、retention、redaction、access control |
| Dashboard | role-based access、residual risk visibility、approval audit |
| Quality Gate | high severity security findingはAIだけでoverride不可 |

## 16.2 Agentic security test catalog

| 観点 | テスト内容 |
|---|---|
| Prompt Injection | RAG文書、メール、PDF、ユーザー入力でagentが乗っ取られないか |
| Tool Misuse | 許可されていないAPIや危険引数を使わないか |
| Excessive Agency | 必要以上の自律判断や副作用を起こさないか |
| Sensitive Information Disclosure | 権限外情報、PII、secretを出さないか |
| Insecure Output Handling | LLM出力をSQL/HTML/shell/APIへ直結しないか |
| Memory Poisoning | 長期記憶や会話履歴が汚染されないか |
| Supply Chain | skill、tool、package、RAG corpusの汚染を検知するか |
| Vector/RAG weakness | 不正chunk、権限外chunk、古いchunkを取得しないか |
| Unbounded Consumption | runaway loop、過剰tool call、token爆発を止めるか |
| Agentic identity / permission | agentの権限継承、過剰権限、tool abuse、権限昇格を検知するか |
| Agentic skill risk | skill packageの権限、依存、workflow、外部tool呼び出しが安全か |
| Performance Abuse | load toolの誤用、過負荷、外部攻撃化を防ぐか |

## 16.3 Risk governance

NIST AI RMFに合わせて、以下へ写像する。

| NIST AI RMF | QAエージェントでの実装 |
|---|---|
| Govern | GatePolicy、RACI、audit、risk acceptance |
| Map | RequirementSpec、RiskSpec、SourceMap、ChangeImpactSpec |
| Measure | EvalSuite、ExecutionEvidence、CoverageModel、QualityAnalyticsSnapshot |
| Manage | GateDecision、ReleaseReadinessReport、ResidualRiskReport、RegressionPromotion |

## 16.4 QAパイプライン自体の防御

本章の対象はテスト対象システムだけではない。**QAパイプライン自身が攻撃対象**である。PR説明文、Jiraチケット、仕様書、コードコメントは信頼できない入力であり、それらがLLMに渡ってgate判断(リスク評価、テストskip判断)に影響する。つまり、細工された入力でリスク評価を下げさせ、テストをskipさせて悪意ある変更を通す攻撃面が存在する(OWASP Agentic Top 10のASI01: Agent Goal Hijackを自システムへ適用した脅威)。

```text
対策:
  - すべてのsource内容を「データであって指示ではない」として扱う
    (instruction / data分離をプロンプト設計とingestion層の両方で強制する)
  - gate判断に影響するLLM出力には、決定的フロア(§12.5)を必ず併用する
  - source trust labelがuntrusted / externalのsourceは、
    リスク評価の引き下げ方向の判断根拠に使用しない
  - gate操作を狙った入力汚染(細工されたPR説明文・チケット・仕様書)を
    security evalの標準ケースに含める
```

---

# 17. Quality Gate設計

## 17.0 Gate導入の段階的enforcement

false blockは開発チームの信頼を非対称に毀損する(1回の誤blockは10回の正しいwarnより強く記憶される)。すべてのgateは以下の3段階で導入し、精度が実証されるまでblockしない。

```text
shadow: 判定を記録するだけ。開発者には見せない。precision / recallを計測する
warn:   PR comment / reportに表示する。blockしない
block:  マージ / リリースを止める

昇格条件(初期値、運用で較正):
  - shadow期間4週間以上
  - gate precision >= 90%
  - 対象チームの明示的合意

降格条件:
  - block段階でfalse blockが繰り返される場合はwarnへ降格し、原因を分析する
```

初期からblock段階で開始してよいgateは以下の4つに限る。

```text
1. Source grounding gate(変更対象のP0/P1のみ)
2. Oracle gate(変更対象のP0/P1のみ。§17.4 grandfathering適用)
3. Evidence gate(失敗時のevidence不足 → inconclusive化)
4. Security gate
```

その他のgate(change impact / test impact / coverage gap / reuse・dedup / performance / reporting系)はshadowまたはwarnから開始する。gateごとにprecisionと開発者フリクション(override申請までの時間、苦情件数)を計測する(§19.7)。

§17.2の閾値および§27.1のblock rulesは、各gateがblock段階へ昇格した後に適用される目標状態である。

## 17.1 Gate種別

| Gate | Block条件 |
|---|---|
| Source grounding gate | 変更対象のP0/P1要求のsource_refsが空 |
| Oracle gate | 変更対象のP0/P1要求にOracleSpecがない(§17.4 grandfathering適用) |
| Testability gate | 観測・制御・reset不能なcritical testをCI昇格しようとしている |
| Evidence gate | 失敗時にstate diff、trace、再現手順がない |
| Security gate | high/critical security findingが未解決 |
| Human review gate | critical riskなのに人間承認がない |
| Flaky gate | CI昇格テストの再現成功率が閾値未満 |
| Judge calibration gate | AI judgeと人間評価の一致率が閾値未満 |
| Regression gate | 過去重大障害の再現テストが失敗 |
| Cost gate | PRあたりのLLM/testコストが予算超過 |
| Change impact gate | P0/P1変更にChangeImpactSpecがない |
| Test impact gate | high-risk変更にTestImpactPlanがない |
| Coverage gap gate | critical CoverageGapが未解決 |
| Reuse / dedup gate | 新規TestAsset生成前にTestAssetIndex検索がない、または重複score閾値超過 |
| Performance risk gate | high PerformanceRiskSpecがあるのに検証skip承認がない |
| Reporting gate / Report completeness gate | ReleaseReadinessReportがないrelease candidate |

## 17.2 初期閾値

| 指標 | 初期目標 |
|---|---:|
| P0/P1 source grounding | 100% |
| P0/P1 OracleSpec定義率 | 100% |
| high-risk evidence completeness | 95%以上 |
| critical security finding open | 0件 |
| CI昇格テストの再現成功率 | 95%以上 |
| AI judge対象のhuman sample review | 10〜20% |
| judge-human agreement | 初期80%以上、改善運用 |
| defect candidate reproduction rate | 80%以上 |
| flaky suspected tests | release blockせず隔離、可視化 |
| regression promotion rate | 月次増加傾向 |
| ChangeImpactSpec生成率 | P0/P1変更で100% |
| high-risk TestImpactPlan生成率 | 100% |
| duplicate test prevention | duplicate score >= 0.90はblock |
| ReleaseReadinessReport生成率 | release candidateで100% |
| high performance risk skip approval | 100% |

上記はいずれも出発点であり、根拠を持たない初期値である。運用開始後4〜8週間の実測データで較正し、変更はGatePolicyのversionとして記録する。較正前の閾値を根拠に恒久的なprocessを固定しない。

## 17.3 GatePolicy追加差分

```text
1. Change impact gate
  - P0/P1変更にChangeImpactSpecがない場合はwarn/block

2. Test impact gate
  - high-risk変更にTestImpactPlanがない場合はblock
  - high-risk testをskipする場合はhuman approval必須

3. Coverage gap gate
  - critical CoverageGapが未解決の場合はblock
  - high CoverageGapはReleaseReadinessReportに必ず表示

4. Reuse / dedup gate
  - 新規TestAsset生成前にTestAssetIndex検索必須
  - duplicate score >= 0.85 の新規テスト生成はblockまたはreview
  - 既存テスト拡張で済む場合、新規E2E生成を原則block

5. Performance risk gate
  - high PerformanceRiskSpecがある場合、性能検証skipには承認が必要
  - SLA違反がある場合はblockまたはwarn

6. Reporting gate
  - ReleaseReadinessReportがないrelease candidateはrelease gate pass不可
  - blocking / warning理由にevidence_refsがない場合はinconclusive

7. Risk acceptance gate
  - high/critical residual riskをreleaseする場合はRiskAcceptance必須
  - RiskAcceptanceにはowner、expiry、followup_action、evidence_refsを必須にする
  - expiry切れのRiskAcceptanceが残るrelease candidateはpass不可
```

## 17.4 Grandfathering(既存機能の扱い)

Source grounding gateとOracle gateを既存プロダクト全体へ即時適用すると、初日からすべてのreleaseがblockされ、gateはoverride常態化により形骸化する。以下の方針を適用する。

```text
- gateの適用対象は「当該release candidateで変更・追加されたP0/P1要求」に限定する
- 変更されていない既存機能はgrandfathering対象とし、gate違反にしない
- 既存機能の要求・oracle棚卸しはバックログ化し、以下の契機で漸進的に解消する:
    - その機能に変更が入ったとき(just-in-time、§5.4.1参照)
    - incidentが発生したとき
    - risk assessmentで高リスクと判定されたとき
- grandfathering対象の残数はdashboardで可視化し、減少傾向を確認する
```

§29のDefinition of Doneにある「すべてのP0/P1要求」は完成形の状態を指す。そこへの到達経路は本方針に従う。

---

# 18. Quality / Release Readiness Dashboard設計

## 18.1 結論

Dashboardは必要。ただし、最初から作り込まない。

```text
MVP:
  Gate Report / PR Commentで十分

本格運用:
  Quality / Release Readiness Dashboardを追加

作らない:
  独立したAgentOps Dashboard
```

## 18.2 Dashboardの目的

```text
- releaseしてよいか判断する
- 何がblock理由なのか見る
- どの要求・リスクが未カバーか見る
- どの変更が未テストか見る
- どのテストを実行・skipしたか見る
- 証跡が足りているか見る
- flakyや失敗分類の傾向を見る
- performance riskがあるか見る
- costと実行時間が暴れていないか見る
```

## 18.3 Dashboard構成

### View 1: Release Readiness

```text
表示項目:
  - release candidate
  - decision: pass / warn / block
  - readiness score
  - blocking reasons
  - warning reasons
  - residual risks
  - required human approvals
  - previous release comparison
```

### View 2: Coverage & Risk

```text
表示項目:
  - P0/P1 source grounding
  - P0/P1 OracleSpec definition rate
  - requirement coverage
  - risk coverage
  - state model coverage
  - MR coverage
  - CoverageGap一覧
```

### View 3: Quality Intelligence

```text
表示項目:
  - impacted requirements
  - impacted risks
  - impacted APIs/components
  - selected tests
  - skipped tests with reason
  - untested changes
  - TestImpactPlan confidence
```

### View 4: Existing Test Asset Reuse

```text
表示項目:
  - reuse candidates
  - tests reused as-is
  - tests extended
  - duplicate tests prevented
  - new tests required
  - maintenance risk
  - obsolete test candidates
```

### View 5: Evidence & Execution

```text
表示項目:
  - pass / fail / inconclusive
  - evidence completeness
  - state diff availability
  - log availability
  - screenshot/video availability
  - reproduction bundle availability
  - sandbox reproducibility
```

### View 6: Failure & Regression

```text
表示項目:
  - product_bug
  - test_bug
  - oracle_issue
  - requirement_ambiguity
  - environment_issue
  - flaky
  - security_finding
  - regression promotion status
```

### View 7: Performance

```text
表示項目:
  - PerformanceRiskSpec一覧
  - performance scenario coverage
  - p95 latency trend
  - SLA violations
  - bottleneck hypotheses
  - PerformanceGateDecision
```

### View 8: Cost & Efficiency

```text
表示項目:
  - LLM cost
  - test runtime
  - cost per detected defect
  - mean time to triage
  - mean time to quality decision
  - skipped test savings
```

### View 9: Minimal Ops Section

独立AgentOps Dashboardは作らない。ただし、品質運用上必要な最小限のOps情報だけDashboard内に置く。

```text
表示項目:
  - skill eval status
  - failed skill runs
  - tool error rate
  - policy violation count
  - human review pending count
  - trace/evidence store ingestion failure
```

## 18.4 Dashboard導入順

```text
Step 1:
  PR Comment / Gate Report

Step 2:
  ReleaseReadinessReportのHTML/Markdown出力

Step 3:
  Internal portal / Grafana / SupersetでDashboard化

Step 4:
  Quality IntelligenceとPerformanceを統合

Step 5:
  Minimal Ops sectionを追加
```

---

# 19. 運用KPI

## 19.1 既存中核KPI

| KPI | 意味 |
|---|---|
| `source_grounding_rate` | artifactがsourceへ紐付いている割合 |
| `oracle_definition_rate` | 要求にOracleSpecがある割合 |
| `deterministic_oracle_rate` | AI judge以外で判定できる割合 |
| `testability_blocker_count` | 観測・制御・reset性の不足数 |
| `evidence_completeness` | trace、state diff、logs等の保存率 |
| `defect_reproduction_rate` | defect候補の再現率 |
| `failure_triage_accuracy` | triage分類の正確性 |
| `regression_promotion_rate` | AI探索結果がCI資産化された割合 |
| `flaky_rate` | 不安定テスト率 |
| `judge_human_agreement` | AI judgeと人間評価の一致率 |
| `pass_at_1` | 1回目成功率 |
| `pass_all_k` | k回全成功率、一貫性指標 |
| `security_violation_rate` | security eval違反率 |
| `cost_per_detected_defect` | 欠陥検出あたりコスト |
| `mean_time_to_triage` | 失敗から分類までの時間 |
| `quality_gate_override_rate` | gate override頻度 |

## 19.2 Analytics / Reporting KPI

```text
release_readiness_score
mean_time_to_quality_decision
gate_report_generation_success_rate
residual_risk_count
release_warning_count
quality_trend_delta
```

## 19.3 Quality Intelligence KPI

```text
change_impact_precision
test_impact_selection_precision
selected_test_failure_yield
skipped_test_escape_rate
coverage_gap_count
coverage_gap_closure_rate
untested_change_count
high_risk_untested_change_count
```

## 19.4 Test Asset Reuse KPI

```text
test_reuse_rate
duplicate_test_prevention_count
new_test_to_existing_extension_ratio
test_gap_closure_rate
maintenance_risk_score
obsolete_test_candidate_count
e2e_overgeneration_prevention_count
```

## 19.5 Performance KPI

```text
performance_risk_detection_count
performance_scenario_coverage
p95_latency_regression_count
sla_violation_count
performance_evidence_completeness
performance_gate_override_rate
performance_bottleneck_resolution_rate
```

## 19.6 Minimal Ops KPI

```text
skill_eval_pass_rate
tool_error_rate
policy_violation_count
human_review_pending_count
trace_ingestion_failure_count
evidence_ingestion_failure_count
```

## 19.7 Gate運用KPI

§17.0の段階的enforcementを運用するための指標である。

```text
gate_precision(gateごと)
gate_false_block_count
gate_override_time(override申請から承認までの時間)
gate_stage(shadow / warn / blockの現在段階)
```

---

# 20. 実装ロードマップ

## Phase 0: Foundation

### 目的

agentを作る前に、契約、証跡、隔離実行、既存テスト資産index、release reporting schemaを作る。

### 実装内容

| 領域 | 成果物 |
|---|---|
| Artifact schema | RequirementSpec、RiskSpec、OracleSpec、ExecutionEvidence |
| Source grounding | SourceMap、source_refs必須化 |
| Evidence Store | metadata DB + object storage |
| Trace Store | run_id、trace_id、tool call log |
| Tool Gateway | allowlist、schema validation、audit |
| Sandbox | ephemeral env、fixture、reset |
| Skill registry | SKILL.md、manifest、version |
| GatePolicy | 最小block条件 |
| Test Asset Foundation | TestAssetIndex、DuplicateTestReport |
| Quality Intelligence Foundation | ChangeImpactSpec、TestImpactPlan、CoverageGap |
| Reporting Foundation | QualityAnalyticsSnapshot、ReleaseReadinessReport |

### 完了条件

```text
- source_refsなしartifactをblockできる
- test実行結果とstate diffをEvidence Storeへ保存できる
- tool callがtrace_id付きで保存される
- sandboxで同じtestを再実行できる
- TestAssetIndexを作成できる
- ChangeImpactSpecを生成できる
- ReleaseReadinessReportのschemaが利用できる
```

## Phase 1: CRUD/業務アプリMVP

### 対象

最初はCRUD/業務アプリの1サービス、1〜2機能に絞る。

### 実装workflow

§4.3 Canonical Quality Workflow(W1〜W19)を、対象1サービス・1〜2機能に対してend-to-endで最小実装する。順序・成果物は§4.3を正とする。

### 実装するagent / skill

| Agent / Skill | 優先度 |
|---|---:|
| Source Grounding Agent | P0 |
| QA Analyst Agent | P0 |
| Testability Agent | P0 |
| Oracle & Evaluation Agent | P0 |
| Execution & Evidence Agent | P0 |
| change-impact-analysis | P0 |
| existing-test-discovery | P0 |
| test-reuse-analysis | P0 |
| duplicate-test-detection | P0 |
| test-impact-selection | P0 |
| coverage-gap-detection | P0/P1 |
| quality-analytics-snapshot | P0 |
| release-readiness-reporting | P0 |
| Automation Agent | P1 |
| Failure Triage Agent | P1 |
| Release Gate Agent | P1 |
| performance-risk-detection | P1 |

### 完了条件

```text
- PR差分から要求・リスク候補をsource付きで生成できる
- ChangeImpactSpecを生成できる
- 既存テスト資産を検索できる
- reuse / extend / new create判断を記録できる
- duplicate test candidateをblock/warnできる
- P0/P1要求にOracleSpecを付与できる
- TestImpactPlanを生成できる
- 不足分だけAPIまたはPlaywrightテストを生成できる
- sandboxで実行できる
- DB/API/event/logの状態差分を保存できる
- 失敗を product bug / test bug / oracle issue / flaky / env issue に分類できる
- ReleaseReadinessReportを出せる
- 人間review後にCI testとして昇格できる
```

## Phase 2: Oracle Model / Quality Gate強化

| 領域 | 成果物 |
|---|---|
| Oracle catalog | Exact/State/Contract/Invariant/Differential/MR/Statistical/Human |
| Requirement-Oracle Matrix | 要求ごとの判定方式 |
| GatePolicy | source/oracle/evidence/security/change impact/reuse/dedup gate |
| Flaky diagnosis | repeated runs、isolation check |
| Regression promotion | defect → deterministic test PR |
| Quality Intelligence | coverage-gap-detection、release-readiness-scoring |
| Dashboard初期版 | Quality / Release Readiness Dashboard初期view |

### 完了条件

```text
- P0/P1 requirements have OracleSpec
- deterministic oracleが使えるところでAI judgeを使わない
- evidence不足の失敗をinconclusiveにできる
- flaky suspected testをrelease gateから隔離できる
- high CoverageGapがReleaseReadinessReportに表示される
- duplicate score閾値超過の新規テスト生成を抑制できる
```

## Phase 3: LLM/RAG/AI agent Eval拡張

| 領域 | 成果物 |
|---|---|
| Eval Harness | EvalSuite、EvalTask、Trial、Grade |
| MR catalog | paraphrase、privilege、groundedness、tool consistency |
| RAG grader | retrieval scope、source consistency |
| Tool call grader | tool name/args/order/side effect |
| Security eval | prompt injection、excessive agency |
| Human calibration | sample review、judge agreement |
| Quality Analytics | Eval結果とReleaseReadinessReport連携 |

### 完了条件

```text
- EvalTaskを20〜50件作成
- 各taskでmultiple trialsを実行
- pass@k / pass^kを出せる
- transcript/outcome/tool callsを保存
- AI judgeのhuman calibrationを開始
- LLM/RAGの重大逸脱をReleaseReadinessReportへ反映できる
```

## Phase 4: Performance Skill導入

```text
追加する:
  - performance-risk-detection
  - PerformanceRiskSpec
  - performance-risk gate
  - performance skip approval
```

### 完了条件

```text
- high performance risk変更にPerformanceRiskSpecが生成される
- 性能検証skipには理由と承認が残る
- PerformanceRiskSpecがReleaseReadinessReportに表示される
```

## Phase 5: 本格Performance Testing / CI/CD統合

| 領域 | 成果物 |
|---|---|
| CI quality gate | PR / nightly / releaseで実行 |
| Online monitoring | production traces sample |
| Incident feedback | incident → EvalTask / regression test |
| Skill eval pipeline | skill変更時に自動eval |
| Dashboard | coverage、risk、cost、flaky、security、performance |
| RACI運用 | owner、approver、risk acceptor |
| Performance Testing | PerformanceScenarioSpec、PerformanceEvidence、PerformanceGateDecision |
| APM連携 | SLA trend、bottleneck analysis |

### 完了条件

```text
- releaseごとにGateDecisionとReleaseReadinessReportを生成
- high severity findingをAIだけでoverrideできない
- incidentがregression/evalへ還流する
- skill変更でskill evalが走る
- dashboardで品質・リスク・コスト・性能を監視できる
- SLA違反をPerformanceGateDecisionへ反映できる
```

## Deferred Phase: Workflow UX / AgentOps

```text
条件付きで検討:
  - 自然言語からWorkflow生成
  - Agent Registry UI
  - AgentOps Dashboard

前提条件:
  - Artifact contractが安定
  - Skill evalが安定
  - GatePolicyが運用済み
  - Dashboardで品質状態が見えている
  - 現場からWorkflow作成の明確な需要がある
```

---

# 21. 4週間MVP Backlog

実装タスクへ分解するときは、Week単位の見出しをそのまま巨大チケットにしない。各Weekはepicとして扱い、schema定義、validator、storage、runner、PR comment、gate wiringを別taskへ分割する。人間は大きなチケットに「あと少し」と書いて沼を作るので、ここは最初から切る。

## Week 1: Contract / Evidence / Test Asset基盤

| Task | DoD |
|---|---|
| Artifact schema定義 | RequirementSpec/RiskSpec/OracleSpec/ExecutionEvidenceがJSON Schema化 |
| SourceMap実装 | PR diffと仕様書sourceをartifactへ紐付け可能 |
| Evidence Store最小版 | run result、logs、state diff保存 |
| trace_id/run_id設計 | 全artifactと実行がtrace可能 |
| Tool Gateway最小版 | API/DB/log toolがallowlist経由で実行 |
| `TestAssetIndex` schema定義 | 既存テストのpath、type、covered requirement/risk、oracle、flake rateを保持できる |
| `ChangeImpactSpec` schema定義 | PR差分から影響component、requirement、risk、APIを保持できる |
| `QualityAnalyticsSnapshot` schema定義 | coverage、execution、evidence、costを集約できる |
| `ReleaseReadinessReport` schema定義 | pass/warn/block、理由、evidence_refsを出せる |

## Week 2: PR差分 → 要求・リスク・Oracle・既存テスト資産

| Task | DoD |
|---|---|
| Source Grounding Agent | source_refs付きで変更影響を出す |
| QA Analyst Agent | RequirementSpec/RiskSpec候補生成 |
| Oracle & Evaluation Agent | OracleSpec候補生成 |
| schema validator | source_refsなし、oracleなしをblock |
| human review UI/PR comment | QA/開発者が承認・修正できる |
| `existing-test-discovery` | repo内テストをindex化できる |
| `test-reuse-analysis` | 新規テスト意図に対して既存テスト候補を出せる |
| `duplicate-test-detection` | 類似テストを検出し、新規生成block/warnできる |
| PR Comment拡張 | 「既存テストを拡張すべきか、新規作成すべきか」を表示できる |

## Week 3: 状態モデル・テスト生成・Quality Intelligence初期版

| Task | DoD |
|---|---|
| StateModel生成 | 対象機能の状態遷移と不変条件が出る |
| TestabilityReport | 観測・制御・reset blockerが出る |
| API test生成 | 1機能で実行可能 |
| Playwright test生成 | 主要happy pathで実行可能 |
| fixture設計 | seed/reset可能 |
| `change-impact-analysis` | PR差分から影響要求・リスク・API候補を出せる |
| `test-impact-selection` | 実行推奨テストとskip候補を出せる |
| `coverage-gap-detection` | 少なくとも要求・リスク・oracle不足をgapとして出せる |
| GatePolicy拡張 | high-risk変更でTestImpactPlanなしをwarn/blockできる |
| `performance-risk-detection` 事前準備（Stretch） | Phase 4開始前にN+1、重いquery、外部API待ち等の検出観点を棚卸しできる。4週間MVPのrelease gate必須条件にはしない |

## Week 4: 実行・証跡・失敗分類・CI昇格・Gate Report

| Task | DoD |
|---|---|
| sandbox実行 | 同じtestを再実行可能 |
| state diff capture | DB/API/event/log差分保存 |
| Failure Triage Agent | product bug/test bug/oracle issue/flake/env分類 |
| regression promotion | review後CI test化 |
| Gate report | source/oracle/evidence/gate結果を出す |
| `quality-analytics-snapshot` | 実行結果、coverage、gap、costを集約できる |
| `release-readiness-reporting` | ReleaseReadinessReportをMarkdown/HTMLで出せる |
| Gate Report拡張 | ChangeImpact、TestImpact、CoverageGap、Reuse/Dedup結果を表示できる。PerformanceRiskはStretch / Phase 4以降で表示 |
| Dashboard最小版 | static reportまたはinternal pageでRelease Readinessを見られる(§18.4 Step 1〜2の範囲。Dashboard基盤構築はしない) |

**MVPスコープ注記:** `performance-risk-detection` はStretch / Phase 4準備扱いとし、4週間MVPのrelease gate必須条件にはしない。性能リスクを検出しても、初期はReleaseReadinessReportの参考情報またはfollow-upとして扱う。

## MVPではやらないこと

```text
- 自然言語からWorkflow生成
- 独立Agent Registry UI
- 独立AgentOps Dashboard
- 本格Performance Testing Agent
- PerformanceRiskSpecを4週間MVPのrelease gate必須条件にすること
- 大規模load testing自動実行
```

---

# 22. 技術スタック案

| 領域 | 推奨 |
|---|---|
| Artifact DB | PostgreSQL |
| Object Store | S3 / GCS / Azure Blob |
| Trace | OpenTelemetry互換 + 独自redaction |
| Queue | Kafka / PubSub / SQS |
| Workflow | Temporal / Durable execution系 |
| Agent runtime | OpenAI Agents SDK相当、または自社orchestrator |
| Skill registry | Git管理 + signed package |
| Schema | JSON Schema / Pydantic / Zod |
| API test | pytest / Playwright API / Postman/Newman |
| UI test | Playwright |
| Property-based | Hypothesis / fast-check |
| Eval Harness | vendor-neutral Python/TypeScript |
| LLM provider | OpenAI / Anthropic / Azure / Gemini / local via adapter |
| Sandbox | container / ephemeral env |
| Secret管理 | Vault / cloud secret manager |
| Dashboard | Grafana / Superset / internal portal |
| CI/CD | GitHub Actions / GitLab CI / Buildkite |
| Test Asset Index | AST parser、test metadata extractor、coverage mapper |
| Code coverage | Istanbul / nyc、coverage.py、JaCoCo、llvm-cov |
| Test Impact | dependency graph、git diff analyzer、coverage map |
| Performance | k6 / JMeter / Gatling / NeoLoad相当ツール |
| APM | Datadog / New Relic / OpenTelemetry / Cloud provider APM |

SWE-agentの研究が示す通り、language model agentsのsoftware engineering task性能はagent-computer interface設計に強く左右される。QAエージェントでもTool Gateway、Sandbox、Repository操作interfaceの設計は、単なる実装詳細ではなく性能と安全性の中核である。([NeurIPS Proceedings][17])

---

# 23. RACI / 運用責任

| 領域 | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Artifact schema | QA Platform | QA Lead | Dev Lead | Product |
| Oracle catalog | QA Architect | QA Lead | Domain SME | Dev |
| StateModel | QA + Dev | Dev Lead | Domain SME | QA |
| EvalSuite | QA Platform | Product/QA Lead | Support/Security | Dev |
| Security eval | Security | Security Lead | QA/Dev | Product |
| Skill package | Skill owner | QA Platform | Dev/QA | Users |
| GatePolicy | QA Lead | Engineering Manager | Security/Product | Teams |
| Risk acceptance | Business/Security owner | Product/Engineering owner | QA | Stakeholders |
| Regression promotion | QA Automation | Dev Lead | QA Analyst | Team |
| Quality Intelligence | QA Platform + Dev Productivity | QA Lead | Dev Lead / Product | Teams |
| Test Asset Index | QA Automation | QA Platform | Dev Teams | QA |
| ReleaseReadinessReport | Release Gate Agent + QA Lead | Engineering Manager | Security/Product | Stakeholders |
| Dashboard | QA Platform | QA Lead | Dev/Product/Security | Teams |
| Performance Risk | Performance/Platform QA | Engineering Manager | SRE/Dev | Product |

AI agentはAccountableになれない。責任主体は人間または組織である。

---

# 24. リリース運用

## 24.1 PR時

以下は§4.3 Canonical Quality WorkflowをPR契機で実行する範囲のviewである。順序の正は§4.3とする。

```text
on PR opened / updated:
  - diff analysis
  - source grounding
  - impacted requirements/risks
  - ChangeImpactSpec生成
  - Existing Test Asset Discovery
  - Reuse / Dedup Analysis
  - CoverageGap検出
  - suggested OracleSpec/TestDesign
  - TestImpactPlan生成
  - affected regression selection
  - lightweight test execution
  - PerformanceRiskSpec生成
  - PR comment with evidence summary
  - ReleaseReadinessReport draft
```

## 24.2 Nightly

```text
nightly:
  - TestAssetIndex更新
  - broader regression suite
  - repeated trials for flaky detection
  - LLM/RAG eval suite
  - security scenario subset
  - performance risk subset評価
  - TestImpactPlan精度評価
  - CoverageGap更新
  - QualityAnalyticsSnapshot更新
  - skill evals if skill changed
  - dashboard update
```

## 24.3 Release candidate

```text
release candidate:
  - ChangeImpactSpec最終確認
  - TestImpactPlan最終確認
  - P0/P1 requirement coverage
  - P0/P1 risk coverage
  - oracle completeness
  - evidence completeness
  - CoverageGap確認
  - DuplicateTestReport確認
  - security gate
  - PerformanceRiskSpec確認
  - PerformanceGateDecision確認
  - judge calibration status
  - ReleaseReadinessReport生成
  - Quality / Release Readiness Dashboard更新
  - residual risk report
  - human approval
```

## 24.4 Production feedback

```text
production:
  - sampled traces
  - user feedback
  - incident detection
  - support ticket mining
  - failed scenario → EvalTask
  - defect → regression test
  - skill failure → skill eval case
  - performance incident → PerformanceScenarioSpec
  - escaped bug → CoverageGap / TestImpactPlan改善
```

---

# 25. 失敗分類

Failure Triage Agentは、失敗を最低限以下に分類する。

| 分類 | 意味 | 次アクション |
|---|---|---|
| `product_bug` | 実装欠陥 | bug ticket、再現test昇格 |
| `test_bug` | test code/fixture誤り | test修正 |
| `oracle_issue` | 判定基準誤り・曖昧 | OracleSpec修正 |
| `requirement_ambiguity` | 要求が曖昧 | 要求ownerへreview |
| `environment_issue` | sandbox/mock/network問題 | infra修正 |
| `flaky` | 非決定的失敗 | repeated run、隔離、原因分析 |
| `security_finding` | 権限・情報漏えい等 | security review |
| `performance_regression` | latency/SLA/throughput劣化 | performance investigation |
| `coverage_gap` | 要求・リスク・oracle・evidence不足 | CoverageGap作成、TestImpactPlan更新 |
| `duplicate_test_issue` | 重複・過剰生成・保守負債 | reuse/dedupルール改善 |
| `inconclusive` | 証跡不足 | evidence capture改善 |

---

# 26. Regression Promotion

AI探索結果は、そのままCIに入れない。最終的には決定的な自動テストへ変換する。

```text
AI agent:
  探索する
  不具合候補を見つける
  状態差分と再現手順を保存する

Test Asset Intelligence:
  既存テストで再現できるか確認する
  duplicate testを防ぐ
  既存テストextendか新規生成かを判断する

Automation skill:
  最小再現手順へ圧縮する
  fixture化する
  deterministic oracleを付ける
  CI testへ変換する

Human reviewer:
  妥当性を確認する
  mainへmergeする
```

---

# 27. 実運用で壊れないための必須ルール

## 27.1 Block rules

以下は各gateがblock段階(§17.0)へ昇格した後の目標状態である。導入時はgateごとにshadow → warn → blockの段階を踏み、§17.4のgrandfathering方針を適用する。

```text
- source_refsがないP0/P1 artifactは使わない
- OracleSpecがないP0/P1 requirementはrelease gate pass不可
- Evidence不足の失敗はfail/passではなくinconclusive
- AI judge単独でcritical riskをpassにしない
- production write toolはQA agentに渡さない
- destructive toolはdry-run + approval必須
- skill変更時はskill eval必須
- sandbox reset不能なtestはCI昇格不可
- security high/critical findingはAIがoverride不可
- 新規TestAsset生成前にTestAssetIndex検索を必須にする
- duplicate score >= 0.90 の新規テスト生成はblock
- high-risk変更でTestImpactPlanがない場合はblock
- critical CoverageGapが未解決の場合はblock
- high PerformanceRiskSpecがある場合、性能検証skipには承認必須
- ReleaseReadinessReportがないrelease candidateはrelease gate pass不可
```

## 27.2 Review rules

| 対象 | Review |
|---|---|
| 新規OracleSpec | QA Architectまたはdomain SME |
| critical RiskSpec | Security/Product/Business owner |
| new skill | Skill owner + QA Platform |
| AI judge rubric | human calibration sample |
| release override | accountable human approval |
| security exception | Security owner approval、期限付きRiskAcceptance |
| high-risk TestImpactPlan skip | QA Lead + domain owner |
| duplicate test override | QA Automation owner |
| critical CoverageGap acceptance | QA Lead + Product/Engineering owner |
| performance SLA override | Engineering Manager + SRE/Performance owner |
| RiskAcceptance作成・更新 | accountable owner + QA Lead。expiryとfollowup必須 |

## 27.3 Versioning rules

| 対象 | version管理 |
|---|---|
| Prompt | prompt_version |
| Skill | semver + changelog |
| EvalSuite | suite_version |
| RAG corpus | corpus_version |
| Policy | policy_version |
| Model | provider/model/version |
| Tool schema | tool_version |
| OracleSpec | oracle_version |
| Fixture | fixture_version |
| TestAssetIndex | index_version |
| CoverageModel | coverage_model_version |
| GatePolicy | gate_policy_version |
| DashboardViewSpec | dashboard_version |
| PerformanceScenarioSpec | performance_scenario_version |
| ResidualRiskReport | residual_risk_report_version |
| RiskAcceptance | risk_acceptance_version |

---

# 28. 不採用・Deferred項目

## 28.1 自然言語からWorkflow生成

### 判断

今回のMVPおよび初期運用では採用しない。

### 理由

```text
- Workflow自由度が高くなりすぎる
- Artifact Contract中心の思想が弱くなる
- 監査しにくい
- ユーザーの自然言語表現に挙動が揺れる
- MVPの検証対象がぼやける
- 既存のPR / CI / Jira triggerで十分に開始できる
```

### 代替案

自然言語生成ではなく、固定Workflow templateを使う。

```text
Workflow templates:
  - PR quality check
  - Requirement to Oracle
  - Change impact to TestImpactPlan
  - Existing test reuse analysis
  - TestDesign to TestAsset
  - Sandbox execution
  - Gate report
  - Regression promotion
```

### Backlog化条件

自然言語からWorkflow生成は、以下が満たされた後に検討する。

```text
- Artifact contractが安定
- Skill evalが安定
- GatePolicyが運用済み
- Dashboardで品質状態が見えている
- 現場からWorkflow作成の明確な需要がある
```

## 28.2 独立Agent Registry

### 判断

独立したAgent Registry画面は作らない。

### 理由

```text
- 既存プランのSkill registryで十分
- agentを主役にすると品質判断が脇役になる
- 初期運用では管理対象が増えるだけ
- 監査に必要なのはagent一覧ではなく、skill version / tool権限 / eval status / evidenceである
```

### 残すもの

```text
Skill registry metadata:
  - skill_id
  - version
  - owner
  - allowed_tools
  - input_schema
  - output_schema
  - schema_version
  - eval_status
  - last_successful_run
  - policy_violation_count
  - policy_violation_metrics
  - changelog
```

## 28.3 独立AgentOps Dashboard

### 判断

独立したAgentOps Dashboardは作らない。

### 理由

```text
- 今回の主語はagent運用ではなく品質判断
- Quality / Release Readiness Dashboardに吸収できる
- 初期からAgentOpsを作ると、管理画面だけ立派なPoCになる
```

### 残すもの

Quality / Release Readiness Dashboard内に、最小Ops sectionだけ置く。

```text
Minimal Ops:
  - skill eval status
  - tool error rate
  - policy violation count
  - failed workflow count
  - human review pending
  - cost / latency
```

---

# 29. 完成形のDefinition of Done

このQAエージェント戦略が「実運用可能」と言える条件は以下である。

```text
1. すべてのP0/P1要求がsourceへ紐付いている
2. すべてのP0/P1要求にOracleSpecがある
3. CRUD/業務アプリではDB/API/event/log/UIの状態観測点が定義されている
4. LLM/RAG/agentではMRSpecとEvalTaskが定義されている
5. 各trialが隔離環境で再実行可能
6. 実行前後の状態差分、tool call、log、grader結果がEvidence Storeに保存される
7. 失敗がproduct bug/test bug/oracle issue/flake/env issue/security findingへ分類される
8. AI探索結果が人間review後に決定的なCI regression testへ昇格できる
9. AI judgeが人間評価で継続校正されている
10. high/critical riskはAI単独でrisk acceptanceできない
11. skill変更時にskill evalが走る
12. releaseごとにGateDecision、ReleaseReadinessReport、ResidualRiskReportが出る
13. high/critical residual riskやperformance skipにはRiskAcceptanceがあり、owner、expiry、followup、evidence_refsが残る
14. PR差分に対してChangeImpactSpecが生成される
15. 新規TestAsset生成前にTestAssetIndex検索が行われる
16. 既存テストのreuse / extend / new create判断が記録される
17. duplicate test candidateが検出され、必要に応じてblock/warnされる
18. TestImpactPlanにselected tests / skipped tests / new tests requiredが記録される
19. CoverageGapがrequirement / risk / oracle / evidence単位で出せる
20. ReleaseReadinessReportがpass / warn / block理由、evidence_refs、ResidualRiskReport参照を持つ
21. DashboardまたはGate ReportでRelease Readinessを確認できる
22. high performance risk変更にPerformanceRiskSpecが生成される
23. performance skipには理由と承認が残る
24. 自然言語Workflow生成なしでもPR / Nightly / Release workflowが回る
25. AgentOps専用画面なしでも、skill eval / policy violation / tool errorは追跡できる
```

---

# 30. 最終アーキテクチャ要約

```text
Source-grounded QA Agent System

Source Connectors
  ↓
Ingestion / Normalization / Redaction
  ↓
Test Asset Intelligence Layer
  - TestAssetIndex
  - Reuse / Dedup
  - TestGapReport
  ↓
Quality Knowledge Base
  - RequirementSpec
  - RiskSpec
  - StateModel
  - OracleSpec
  - MRSpec
  - PolicyModel
  - CoverageModel
  - TestabilityReport
  - ChangeImpactSpec
  - TestImpactPlan
  - CoverageGap
  - PerformanceRiskSpec
  ↓
Thin Quality Orchestrator
  - contract validation
  - skill routing
  - handoff control
  - gate enforcement
  - human routing
  - reuse / dedup enforcement
  - performance risk routing
  ↓
Skill Runtime
  - SKILL.md
  - schema
  - validators
  - scripts
  - evals
  - ownership
  - quality intelligence skills
  - analytics/reporting skills
  - performance skills
  ↓
Specialist Agents
  - source grounding
  - QA analysis
  - testability
  - architecture
  - oracle/eval
  - automation
  - execution/evidence
  - triage
  - security
  - release gate
  - quality intelligence
  - performance later
  ↓
Tool Gateway
  - allowlist
  - authz
  - guardrails
  - audit
  ↓
Execution Sandbox
  - isolated env
  - deterministic fixture
  - reset
  - mock external services
  - performance sandbox later
  ↓
Trace & Evidence Store
  - transcript
  - tool call
  - state diff
  - logs
  - grader
  - human review
  - QualityAnalyticsSnapshot
  - ReleaseReadinessReport
  - PerformanceEvidence
  ↓
Quality Gate & Reporting
  - GateDecision
  - ReleaseReadinessReport
  - residual risk
  - regression promotion
  - Quality / Release Readiness Dashboard
```

---

# 31. 最終提案

まず作るべきものは、万能QA Agentではない。

作るべきものは以下である。

> **Source-grounded Contract + Oracle + Isolated Execution + Evidence + Existing Test Reuse + Quality Intelligence + Release Readiness MVP**

最初のMVPは、§4.3 Canonical Quality Workflow(W1〜W19)を実在する1サービス・1〜2機能に対してend-to-endで最小実装することに絞る。gateは§17.0の段階的enforcementに従い、初期block gateは4つ(source grounding / oracle / evidence / security)に限定する。

最終方針はこれである。

> **AIにテストを増やさせるのではなく、変更影響、既存資産、カバレッジギャップ、証跡、性能リスク、残リスクをつないで、リリース判断の質を上げる。**

AIに品質判断を委ねるのではなく、品質判断が再現可能・監査可能・改善可能になるように、AIを契約、オラクル、証跡、評価、人間校正、既存資産活用、Release Readinessの中に閉じ込めて使う。

これが、実運用可能なQAエージェント戦略である。

---

# References

> 以下は統合元文書およびセルフレビューで確認した外部参照を保持したもの。

[1]: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents "Demystifying evals for AI agents | Anthropic"
[2]: https://developers.openai.com/api/docs/guides/evals "Working with evals | OpenAI API"
[3]: https://developers.openai.com/api/docs/guides/graders "Graders | OpenAI API"
[4]: https://developers.openai.com/api/docs/guides/evaluation-best-practices "Evaluation best practices | OpenAI API"
[5]: https://openai.github.io/openai-agents-python/ "OpenAI Agents SDK"
[6]: https://www.anthropic.com/research/building-effective-agents "Building Effective AI Agents | Anthropic"
[7]: https://docs.anthropic.com/en/docs/claude-code/skills "Extend Claude with skills - Claude Code Docs"
[8]: https://www.iso.org/standard/79428.html "ISO/IEC/IEEE 29119-2:2021 - Software testing"
[9]: https://pure.kaist.ac.kr/en/publications/the-oracle-problem-in-software-testing-a-survey/ "The oracle problem in software testing: A survey"
[10]: https://vuir.vu.edu.au/33046/1/TSEmt.pdf "How effectively does metamorphic testing alleviate the oracle problem?"
[11]: https://owasp.org/www-project-top-10-for-large-language-model-applications/ "OWASP Top 10 for Large Language Model Applications"
[12]: https://www.nist.gov/itl/ai-risk-management-framework "AI Risk Management Framework | NIST"
[13]: https://openai.github.io/openai-agents-python/handoffs/ "Handoffs - OpenAI Agents SDK"
[14]: https://openai.github.io/openai-agents-python/guardrails/ "Guardrails - OpenAI Agents SDK"
[15]: https://developers.openai.com/blog/eval-skills "Testing Agent Skills Systematically with Evals | OpenAI Developers"
[16]: https://openai.github.io/openai-agents-python/tracing/ "Tracing - OpenAI Agents SDK"
[17]: https://proceedings.neurips.cc/paper_files/paper/2024/hash/5a7c947568c1b1328ccc5230172e1e7c-Abstract-Conference.html "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering"
[18]: https://www.tricentis.com/products/ai-workspace "AI Workspace for Agentic Quality Engineering"
[19]: https://www.tricentis.com/products/unified-test-management-qtest "AI-powered test management – qTest"
[20]: https://www.tricentis.com/products/quality-intelligence-sealights "Software quality intelligence – Tricentis SeaLights"
[21]: https://www.tricentis.com/products/performance-testing-neoload "AI-driven automated performance & load testing tool"

[22]: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ "OWASP Top 10 for Agentic Applications 2026"
[23]: https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html "AI Agent Security Cheat Sheet"
