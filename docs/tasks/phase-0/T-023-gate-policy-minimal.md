---
task_id: T-023
epic: skill-registry-gatepolicy
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-002, T-003]
---

# T-023: GatePolicy最小版(gate-policy.yaml + CHANGELOG)

## 目的

versioned configとしてのGatePolicy最小版を作る。gate実行(wiring)はPhase 1以降で、Phase 0はpolicy定義とその機械検証まで。

## 参照

- 計画: §3 WS-E
- North Star: §17.0(段階的enforcement)、§17.1(Gate種別)、§17.2(初期閾値。較正前の出発点である点に注意)、§17.3(追加差分)
- `policies/README.md`

## DoD

- [ ] `policies/gate-policy.yaml` が存在し、§17.1の各gateについて段階(shadow / warn / block)と閾値を定義している
- [ ] block段階は初期4 gate(source grounding / oracle / evidence / security)のみで、他はshadowまたはwarnになっている(§17.0。テストで検証)
- [ ] policy fileを検証するschemaがあり、validationがテストでpassする
- [ ] `policies/CHANGELOG.md` に初版entry(version、日付、根拠として§17.0参照)が記録されている

## 検証方法・根拠

- DoD 1 (`policies/gate-policy.yaml`): `policy_version: "0.1.0"` のversioned configとして追加。`tests/test_gate_policy.py::TestGatePolicy::test_policy_defines_every_section_17_1_gate_once` で§17.1の全gate IDが過不足なく定義されること、`test_each_section_17_1_gate_has_stage_and_thresholds` で各gateが `stage` と `thresholds` を持つことを検証。
- DoD 2 (初期block 4 gateのみ): `tests/test_gate_policy.py::TestGatePolicy::test_only_initial_four_gates_start_in_block_stage` でblock段階が `source_grounding` / `oracle` / `evidence` / `security` のみであることを検証。`test_non_initial_block_gates_start_in_shadow_or_warn` でその他gateがshadowまたはwarnで開始することを検証。
- DoD 3 (policy schema validation): `policies/gate-policy.schema.json` を追加。GatePolicyはartifactではなくversioned configのため `schemas/` ではなく `policies/` 配下に置き、生成モデル対象外とした。`tests/test_gate_policy.py::TestGatePolicySchemaItself::*` でschema自体、`test_gate_policy_yaml_passes_schema` でYAML validation、`test_type_or_value_violation_fails` / `test_missing_required_field_fails` で未知stage・閾値型違反・必須欠落がfailすることを検証。
- DoD 4 (`policies/CHANGELOG.md`): 初版entry `0.1.0 - 2026-07-03` を追加し、North Star §17.0に従う初期block 4 gate限定と§17.2の較正前初期値であることを記録。
- 実行結果:
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_gate_policy.py -q` → `17 passed`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest` → `545 passed`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff check .` → `All checks passed!`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff format --check .` → `86 files already formatted`

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし(§17.0-§17.3に沿った最小policy定義であり、North Starからの逸脱や新たなgate較正知見はなし)
