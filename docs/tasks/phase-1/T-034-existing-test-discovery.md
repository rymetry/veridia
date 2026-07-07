---
task_id: T-034
epic: test-asset-reuse
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-024]
---

# T-034: `existing-test-discovery`(対象repoのTestAssetIndex生成)

## 目的

対象サービスrepoの既存テスト資産を走査してTestAssetIndexを生成する(W4)。Phase 0 T-009のgeneratorをveridia以外の実repoへ適用し、対象repoのテスト構成に必要な拡張を加える。Phase 1完了条件「既存テスト資産を検索できる」をカバーする。

## 参照

- 計画: §5(test-asset-reuse)
- North Star: §7.4(existing-test-discovery)、§6.13(TestAssetIndex)、§5.3(Test Asset Intelligence Layer)
- Phase 0: T-009(generator実装。決定的・LLM不使用)

## DoD

- [ ] T-009のgeneratorが対象サービスrepoでTestAssetIndexを生成できる(対象repoのテスト規約に合わせたwalker/type判定の拡張を含む。拡張は設定またはプラグイン的に分離し、generatorのcoreにrepo固有ロジックをハードコードしない)
- [ ] 生成物がartifact_validatorをpassし、対象repoの実テストが1件以上 path / type付きで含まれる
- [ ] 生成したTestAssetIndexに対して、キーワード・対象file・typeで既存テストを検索できる(最小の検索インターフェース。CLI 1発で確認)
- [ ] `covered_requirements` 等のPhase 1で埋まるfieldと未収集fieldの扱いが生成物とREADMEで区別されている(T-009の方式を踏襲)
- [ ] `uv run pytest` がpassする(対象repoが手元にない環境ではfixture repoで代替できるテスト構成にする)

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
