# Phase 1 タスク一覧(集約ビュー)

frontmatterから再生成する集約ビュー。**手で編集しない**(statusの正本は各タスクファイル。`docs/tasks/README.md` 参照)。

生成日: 2026-07-07 / 全33タスク(not_started: 33)

| task_id | epic | status | blocked_by | タイトル |
|---|---|---|---|---|
| [T-024](T-024-target-service-decision.md) | phase1-setup | not_started | - | OQ-2 対象サービス・機能の決定 |
| [T-025](T-025-adr-llm-skill-execution.md) | phase1-setup | not_started | - | ADR-0005 LLM skill実行方式の決定(OQ-5) |
| [T-026](T-026-source-connector-minimal.md) | phase1-setup | not_started | T-024 | Source Connector最小版(OQ-4決定 + 対象repo PR diff取得) |
| [T-027](T-027-skill-runner-minimal.md) | phase1-setup | not_started | T-025 | skill実行基盤最小版(skill runner) |
| [T-028](T-028-source-map-schema.md) | grounding-oracle | not_started | - | SourceMap schema定義 |
| [T-029](T-029-source-grounding-skill.md) | grounding-oracle | not_started | T-026, T-027, T-028 | `source-grounding` skill(W1: PR diff → SourceMap) |
| [T-030](T-030-requirement-risk-analysis-skill.md) | grounding-oracle | not_started | T-029 | `requirement-risk-analysis` skill(W2: 要求・リスク候補生成) |
| [T-031](T-031-human-review-flow.md) | grounding-oracle | not_started | T-030 | human reviewフロー + source grounding gate配線 |
| [T-032](T-032-oracle-selection-skill.md) | grounding-oracle | not_started | T-030, T-031 | `oracle-selection` skill(W7: P0/P1要求へOracleSpec候補付与) |
| [T-033](T-033-reuse-dedup-schemas.md) | test-asset-reuse | not_started | - | TestReuseCandidate / DuplicateTestReport schema定義 |
| [T-034](T-034-existing-test-discovery.md) | test-asset-reuse | not_started | T-024 | `existing-test-discovery`(対象repoのTestAssetIndex生成) |
| [T-035](T-035-test-reuse-analysis-skill.md) | test-asset-reuse | not_started | T-027, T-031, T-033, T-034 | `test-reuse-analysis` skill(reuse / extend / new判断) |
| [T-036](T-036-duplicate-test-detection-skill.md) | test-asset-reuse | not_started | T-033, T-034 | `duplicate-test-detection` skill + dedup gate(shadow)配線 |
| [T-037](T-037-modeling-schemas.md) | modeling-generation | not_started | - | StateModel / TestabilityReport schema定義 |
| [T-038](T-038-state-modeling-skill.md) | modeling-generation | not_started | T-027, T-031, T-037 | `state-modeling` skill(W6: StateModel生成) |
| [T-039](T-039-testability-analysis-skill.md) | modeling-generation | not_started | T-031, T-037 | `testability-analysis` skill(W8: TestabilityReport) |
| [T-040](T-040-impact-gap-schemas.md) | quality-intelligence | not_started | - | TestImpactPlan / CoverageGap schema定義 |
| [T-041](T-041-change-impact-analysis-skill.md) | quality-intelligence | not_started | T-027, T-031 | `change-impact-analysis` skill(W3: 意味的マッピング) |
| [T-042](T-042-coverage-gap-detection-skill.md) | quality-intelligence | not_started | T-032, T-034, T-040 | `coverage-gap-detection` skill(W10: CoverageGap生成) |
| [T-043](T-043-test-impact-selection-skill.md) | quality-intelligence | not_started | T-034, T-040, T-041 | `test-impact-selection` skill(W11: TestImpactPlan生成) |
| [T-044](T-044-performance-risk-detection-prep.md) | quality-intelligence | not_started | T-024 | `performance-risk-detection` 事前準備(Stretch) |
| [T-045](T-045-api-test-generation.md) | modeling-generation | not_started | T-032, T-035, T-038, T-042 | APIテスト生成(W12: 不足分のみ・1機能で実行可能) |
| [T-046](T-046-playwright-test-generation.md) | modeling-generation | not_started | T-045 | Playwrightテスト生成(W12: 主要happy path) |
| [T-047](T-047-target-sandbox-integration.md) | execution-evidence | not_started | T-024 | 対象サービスsandbox統合(起動・fixture seed・reset) |
| [T-048](T-048-sandbox-execution-evidence.md) | execution-evidence | not_started | T-045, T-046, T-047 | 生成テストのsandbox実行 + ExecutionEvidence保存(W14) |
| [T-049](T-049-state-diff-capture.md) | execution-evidence | not_started | T-039, T-048 | state diff capture(DB / API / event / log差分の保存) |
| [T-050](T-050-failure-triage-skill.md) | execution-evidence | not_started | T-027, T-048 | `failure-triage` skill(W15: 失敗5分類) |
| [T-051](T-051-regression-promotion.md) | execution-evidence | not_started | T-050 | regression promotion(W19: human review後のCI test昇格) |
| [T-052](T-052-quality-analytics-snapshot-skill.md) | reporting-gate | not_started | T-048 | `quality-analytics-snapshot`(W16: 品質状態の集約) |
| [T-053](T-053-release-readiness-reporting-skill.md) | reporting-gate | not_started | T-052 | `release-readiness-reporting`(W17: ReleaseReadinessReport生成) |
| [T-054](T-054-gate-decision-enforcement.md) | reporting-gate | not_started | T-032, T-036, T-043, T-049, T-053 | GateDecision schema + gate段階運用の配線(W18) |
| [T-055](T-055-dashboard-minimal.md) | reporting-gate | not_started | T-053 | Dashboard最小版(§18.4 Step 1〜2) |
| [T-056](T-056-e2e-workflow-verification.md) | reporting-gate | not_started | T-046, T-051, T-054, T-055 | W1〜W19 end-to-end実証と完了条件の記帳 |

## epic別内訳

| epic(計画mdのepic分解) | タスク数 |
|---|---:|
| phase1-setup(着手前提) | 4 |
| grounding-oracle(Week 2) | 5 |
| test-asset-reuse(Week 2) | 4 |
| modeling-generation(Week 3) | 5 |
| quality-intelligence(Week 3) | 5 |
| execution-evidence(Week 4) | 5 |
| reporting-gate(Week 4) | 5 |

全タスクdone後もPhase完了とは判定しない(計画mdの完了条件チェックリストが正、AGENTS.md変更ルール6)。
