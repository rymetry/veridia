---
task_id: T-055
epic: reporting-gate
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-053]
---

# T-055: Dashboard最小版(§18.4 Step 1〜2)

## 目的

Release Readinessを人間が一覧できる最小のDashboardを作る。範囲は§18.4のStep 1〜2(static reportまたはinternal page)に限定し、Dashboard基盤構築はしない(§21 Week 4の制約)。

## 参照

- 計画: §5(reporting-gate)
- North Star: §18.1〜18.2(目的)、§18.3 View 1(Release Readiness)、§18.4(導入順Step 1〜2)

## DoD

- [ ] 最新のReleaseReadinessReport(T-053のMarkdown/HTML出力)を起点に、run履歴を一覧できるstaticページまたはindexが生成される(静的生成でよい。サーバ・DB・フロントエンド基盤を新設しない)
- [ ] View 1(Release Readiness)相当の情報(pass / warn / block、主要理由、evidenceへのリンク)が1画面で確認できる
- [ ] 生成がコマンド1発で再実行でき、決定的である(同一入力→同一出力のテスト)
- [ ] §18.4 Step 3以降に踏み込んでいないことを確認する: §18.4を開き、Step 3以降に列挙された要素が成果物に含まれないことを照合し、照合結果を「検証方法・根拠」節に記す(スコープ逸脱防止)

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
