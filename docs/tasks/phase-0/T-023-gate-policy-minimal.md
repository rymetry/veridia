---
task_id: T-023
epic: skill-registry-gatepolicy
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
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

(完了時に記入。想定: policy validationのテスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
