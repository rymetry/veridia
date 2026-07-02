---
task_id: T-009
epic: artifact-schema
plan_ref: phase-0-foundation.md#2-完了条件
status: not_started
owner:
blocked_by: [T-006, T-008]
---

# T-009: TestAssetIndex generator最小版

## 目的

対象repoのテスト資産を走査してTestAssetIndexを生成する。計画§2完了条件「対象repoからTestAssetIndexを生成できる」をカバーし、schemaを実データで検証する。OQ-4(対象repo)未決の間はveridia自身をダミー対象とする(計画§6)。LLM不使用の決定的実装(計画§1のスコープ)。

## 参照

- 計画: §2 完了条件、§6 リスクと未確定事項(OQ-4)
- North Star: §6.13、§5.3(Test Asset Intelligence Layer)

## DoD

- [ ] コマンド1発で指定repoのテストファイルを走査し、TestAssetIndex JSONを生成できる(veridia自身を対象に実行して確認)
- [ ] 生成物に1件以上のテスト資産(path / type)が含まれ、T-008 validatorをpassする(テストで実証)
- [ ] Phase 0で取得できないfield(covered requirement / flake rate等)の扱い(null / 未収集の区別)が生成物とREADMEに明記されている

## 検証方法・根拠

(完了時に記入。想定: 生成コマンドの実行ログとvalidator結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
