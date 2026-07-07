---
task_id: T-046
epic: modeling-generation
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-045]
---

# T-046: Playwrightテスト生成(W12: 主要happy path)

## 目的

対象機能の主要happy pathについてPlaywright E2Eテストを生成する(W12)。T-045と同じ「不足分のみ」原則・生成パイプラインを再利用し、UI層とbackend状態の整合検証(§3.1のUI/E2E)を最小範囲で実現する。

## 参照

- 計画: §5(modeling-generation)
- North Star: §3.1(UI / E2E)、§10.3(状態テスト例)、§21 Week 3(Playwright test生成のDoD)

## DoD

- [ ] T-045の生成パイプライン(gap駆動・reuse尊重・candidate扱い)を再利用してPlaywrightテストを生成できる(生成抑制ロジックの重複実装をしない)
- [ ] 対象機能の主要happy path 1本以上が生成され、実行可能である(§21 Week 3のDoD「主要happy pathで実行可能」。実行はsandbox統合後でよいが、少なくともPlaywright構文として妥当でdry runが通る)
- [ ] UI操作の結果としてのbackend状態(DB / API)の検証がテストに含まれる(画面表示のみのassertで終わらない。§10.1)
- [ ] 生成テストのmetadataがTestAssetIndexへ反映される
- [ ] fake LLMでの構造検証のpytestがpassする

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
