# Phase 0: Foundation 実装計画

対応: North Star §20 Phase 0、§21 Week 1
Phaseレベルstatusの正本: [00-overview.md](00-overview.md)(status値はここに複製しない。変更ルール3)

## 1. 目的とスコープ

agentを作る前に、契約(schema)、証跡、隔離実行、既存テスト資産index、release reporting schemaの基盤を作る(§20 Phase 0)。

やらないこと: agent実装、テスト生成、LLM呼び出しを伴う機能(すべてPhase 1)、§6全27 artifactの一括schema化(just-in-time、§5.4.1)。

## 2. 完了条件

§20 Phase 0の完了条件を検証可能な形で再掲する(検証方法まで書くのが計画の責務のため、ここは複製ではなく具体化)。

検証記録: 2026-07-03 Phase review(/phase-review)で全項目を再実行して確認。全体では `uv run pytest` 545 passed、`scripts/gen_models.py --check` ok(schema→生成モデルdrift無し)、`ruff check` / `ruff format --check` ともにpass。

- [x] source_refsが空のartifactをvalidatorがrejectする(テストで実証)— [T-008](../tasks/phase-0/T-008-artifact-validator.md)。`tests/test_artifact_validator.py::test_validator_rejects_empty_or_missing_source_refs`(空 `[]` と欠落の2ケース。2026-07-03再実行: 2 passed)
- [x] test実行結果とstate diffをEvidence Storeへ保存し、読み出せる — [T-013](../tasks/phase-0/T-013-evidence-store-minimal.md) / [T-020](../tasks/phase-0/T-020-sandbox-runner-determinism.md)。`tests/test_evidence_store.py::test_save_and_read_execution_evidence_by_artifact_id_and_trace_id`(state_diffのround-trip)、`tests/test_sandbox_runner.py::test_each_run_has_ids_and_can_be_read_from_evidence_store`(runner実行結果の保存→読み出し)
- [x] tool callがtrace_id付きで保存される — [T-016](../tasks/phase-0/T-016-tool-gateway-audit-log.md)。`tests/test_tool_gateway_audit.py::test_gateway_tool_call_is_saved_with_trace_id_and_redacted_args`(reject時のerror status保存、複数callのtrace共有も同ファイルで検証。2026-07-03再実行: 4 passed)
- [x] sandboxで同じtestを2回実行し、同一結果になる — [T-020](../tasks/phase-0/T-020-sandbox-runner-determinism.md)。`tests/test_sandbox_runner.py::test_same_sample_test_run_twice_has_same_result_and_state_diff`(result・state_diffの完全一致を検証)
- [x] 対象repoからTestAssetIndexを生成できる — [T-009](../tasks/phase-0/T-009-test-asset-index-generator.md)。2026-07-03実再実行: `uv run python -m test_asset_index_generator . <out> --repository veridia --branch main` でveridia自身(§6のダミー対象)から23 assetのindexを生成し、`python -m artifact_validator` でvalid
- [x] PR diffからChangeImpactSpec(候補レベル)を生成できる — [T-010](../tasks/phase-0/T-010-change-impact-generator.md)。2026-07-03実再実行: 実commit diff(`git diff HEAD~1 HEAD`、8dcf7f3、646行)から `uv run python -m change_impact_generator` でchanged_files 7件・候補レベル(`analysis_status: candidate_path_only_phase_0`)のartifactを生成し、validatorでvalid
- [x] ReleaseReadinessReportのschemaがvalidationを通る — [T-007](../tasks/phase-0/T-007-reporting-schemas.md)。`tests/test_reporting_schemas.py`(2026-07-03再実行: 62 passed)— warn sample、pass/warn/block全decision、schema埋め込みexamplesのvalidationを含む

## 3. ワークストリーム分割

タスクのepicはこのIDを使う。

| WS | epic ID | 内容 | 主な§ |
|---|---|---|---|
| WS-A | `artifact-schema` | ArtifactBase + コアspec(RequirementSpec / RiskSpec / OracleSpec / ExecutionEvidence)+ 基盤spec(TestAssetIndex / ChangeImpactSpec / QualityAnalyticsSnapshot / ReleaseReadinessReport)のJSON Schema化とvalidator、および完了条件検証用の最小generator(TestAssetIndex / ChangeImpactSpec候補) | §6 |
| WS-B | `evidence-trace-store` | Evidence Store最小版(metadata DB + object storage)、trace_id / run_id設計 | §15 |
| WS-C | `tool-gateway` | allowlist、schema validation、audit logの最小版 | §5.6 |
| WS-D | `sandbox` | ephemeral env、fixture seed、reset | §5.7 |
| WS-E | `skill-registry-gatepolicy` | skill package規約(`qa-skills/README.md`)、registry metadata(§28.2)、GatePolicy最小版(`policies/gate-policy.yaml`、初期block 4 gateのみ §17.0) | §7, §17 |

## 4. 依存と着手順序

```
WS-A(schema)
  ├→ WS-B(evidenceはExecutionEvidence schemaに依存)
  ├→ WS-E(GatePolicyはartifact contractに依存)
  └→ WS-C / WS-D(並行可。schemaへの依存は薄い)
```

WS-Aから着手する。WS-C / WS-DはWS-B完了を待たず並行してよい。

## 5. 技術選定(ADR起票が必要な決定)

§22の推奨から実際に採用するものをADRで確定する。Phase 0で必要な決定のみ:

- 実装言語とschema lib(Python+Pydantic / TypeScript+Zod)→ OQ-1
- Artifact DB / object storeのローカル開発構成 → OQ-3
- sandboxの実現方式(container構成)

Queue / Temporal / APM等(§22)はPhase 0では決定しない。

## 6. リスクと未確定事項

- OQ-1 / OQ-3(00-overview参照)が未決のままWS-Aを始めると手戻りする。**最初のタスクはADR-0002(言語・schema lib)とする**
- TestAssetIndexの対象repo(OQ-4)が未決の間は、veridia自身をダミー対象として実装してよい
- スコープクリープ注意: Tool Gateway / Sandboxは§5.6 / §5.7の全機能表ではなく、完了条件を満たす最小実装に留める

## 7. タスク分解方針

`docs/tasks/phase-0/` に1タスク=1ファイルで分解する(`docs/tasks/README.md` 参照)。分解の粒度は§21の指示に従い、Week見出しを巨大チケットにしない(schema定義、validator、storage、runnerを別タスクに切る)。
