# Phase 0 タスク一覧(集約ビュー)

frontmatterから再生成する集約ビュー。**手で編集しない**(statusの正本は各タスクファイル。`docs/tasks/README.md` 参照)。

生成日: 2026-07-02 / 全23タスク(not_started: 23)

| task_id | epic | status | blocked_by | タイトル |
|---|---|---|---|---|
| [T-001](T-001-adr-0002-language-schema-lib.md) | artifact-schema | not_started | - | ADR-0002 実装言語・schema lib決定 |
| [T-002](T-002-dev-scaffolding.md) | artifact-schema | not_started | T-001 | 開発環境scaffolding(build / test / lint) |
| [T-003](T-003-artifact-base-schema.md) | artifact-schema | not_started | T-001, T-002 | ArtifactBase JSON Schema定義 |
| [T-004](T-004-core-spec-schemas.md) | artifact-schema | not_started | T-003 | コアspec schema定義(RequirementSpec / RiskSpec / OracleSpec) |
| [T-005](T-005-execution-evidence-schema.md) | artifact-schema | not_started | T-003 | ExecutionEvidence schema定義 |
| [T-006](T-006-test-asset-impact-schemas.md) | artifact-schema | not_started | T-003 | 基盤spec schema定義(TestAssetIndex / ChangeImpactSpec) |
| [T-007](T-007-reporting-schemas.md) | artifact-schema | not_started | T-003 | 基盤spec schema定義(QualityAnalyticsSnapshot / ReleaseReadinessReport) |
| [T-008](T-008-artifact-validator.md) | artifact-schema | not_started | T-002, T-003, T-004, T-005, T-006, T-007 | Artifact validator実装(source_refs必須化を含む) |
| [T-009](T-009-test-asset-index-generator.md) | artifact-schema | not_started | T-006, T-008 | TestAssetIndex generator最小版 |
| [T-010](T-010-change-impact-generator.md) | artifact-schema | not_started | T-006, T-008 | ChangeImpactSpec候補generator最小版 |
| [T-011](T-011-adr-evidence-store-stack.md) | evidence-trace-store | not_started | T-001 | ADR起票 Evidence Store / Trace Store構成決定 |
| [T-012](T-012-trace-run-id-design.md) | evidence-trace-store | not_started | T-002, T-003 | trace_id / run_id設計と生成ユーティリティ |
| [T-013](T-013-evidence-store-minimal.md) | evidence-trace-store | not_started | T-005, T-008, T-011, T-012 | Evidence Store最小版(保存・読み出しAPI) |
| [T-014](T-014-trace-store-minimal.md) | evidence-trace-store | not_started | T-011, T-012 | Trace Store最小版(trace record保存・参照) |
| [T-015](T-015-tool-gateway-minimal.md) | tool-gateway | not_started | T-002 | Tool Gateway最小版(allowlist + schema validation) |
| [T-016](T-016-tool-gateway-audit-log.md) | tool-gateway | not_started | T-014, T-015 | Tool Gateway audit log(trace_id付きtool call保存) |
| [T-017](T-017-adr-sandbox-runtime.md) | sandbox | not_started | - | ADR起票 sandbox実現方式決定 |
| [T-018](T-018-sandbox-ephemeral-env.md) | sandbox | not_started | T-002, T-017 | sandbox ephemeral env(作成・破棄・reset) |
| [T-019](T-019-sandbox-fixture-seed.md) | sandbox | not_started | T-018 | fixture seed機構とdeterministic clock |
| [T-020](T-020-sandbox-runner-determinism.md) | sandbox | not_started | T-013, T-019 | sandbox test runner最小版と決定性検証 |
| [T-021](T-021-skill-package-convention.md) | skill-registry-gatepolicy | not_started | T-002 | skill package規約とtemplate skeleton |
| [T-022](T-022-skill-registry-metadata.md) | skill-registry-gatepolicy | not_started | T-021 | skill registry metadata定義 |
| [T-023](T-023-gate-policy-minimal.md) | skill-registry-gatepolicy | not_started | T-002, T-003 | GatePolicy最小版(gate-policy.yaml + CHANGELOG) |

## epic別内訳

| epic(計画§3) | タスク数 |
|---|---:|
| artifact-schema(WS-A) | 10 |
| evidence-trace-store(WS-B) | 4 |
| tool-gateway(WS-C) | 2 |
| sandbox(WS-D) | 4 |
| skill-registry-gatepolicy(WS-E) | 3 |

全タスクdone後もPhase完了とは判定しない(計画mdの完了条件チェックリストが正、AGENTS.md変更ルール6)。
