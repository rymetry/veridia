---
task_id: T-006
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-003]
---

# T-006: 基盤spec schema定義(TestAssetIndex / ChangeImpactSpec)

## 目的

Test Asset Foundation / Quality Intelligence Foundationの入口となる2 artifactのJSON Schemaを定義する。T-009 / T-010のgeneratorの出力契約。

## 参照

- 計画: §3 WS-A
- North Star: §6.13(TestAssetIndex)、§6.9(ChangeImpactSpec)

## DoD

- [ ] `schemas/test-asset-index.schema.json` / `change-impact-spec.schema.json` が存在し、`allOf` でartifact-baseを継承している
- [ ] TestAssetIndexが既存テストのpath / type / covered requirement・risk / oracle / flake rateを保持できる(§21 Week 1のDoD準拠。サンプルinstanceで確認)
- [ ] ChangeImpactSpecが影響component / requirement / risk / APIを保持できる(サンプルinstanceで確認)
- [ ] 各schemaについて、有効サンプルがpassし、不正サンプルがfailするテストがある

## 検証方法・根拠

- DoD 1: `schemas/test-asset-index.schema.json` / `schemas/change-impact-spec.schema.json` を追加し、`tests/test_test_asset_impact_schemas.py` の `test_inherits_artifact_base_via_allof` で `artifact-base.schema.json` の `allOf` 継承を検証。結果: pass。
- DoD 2: TestAssetIndexの§6.13相当サンプルをschema `examples` と `make_test_asset_index_instance()` に置き、path / type / covered requirement・risk / oracle / flake rateを保持できることを検証。加えて、T-009 Phase 0 generator相当として `covered_requirements` / `covered_risks` / `oracle_refs` が空配列、`stability.flake_rate` がnullのassetを持つinstanceもpassすることを確認。代表的な不正値(test_type enum違反、path欠落、oracle_refsキー欠落、flake_rate範囲外)はfailすることを確認。結果: pass。
- DoD 3: ChangeImpactSpecの§6.9相当サンプルをschema `examples` と `make_change_impact_spec_instance()` に置き、影響component / requirement / risk / APIを保持できることを検証。加えて、T-010 Phase 0候補generator相当として `impacted_requirements` / `impacted_risks` / `impacted_apis` が空配列のinstanceもpassすることを確認。代表的な不正値(change_type enum違反、path欠落、impacted_apis型違反、changed_components空配列)はfailすることを確認。結果: pass。
- DoD 4: `tests/test_test_asset_impact_schemas.py` で有効サンプル、schema埋め込みexample、ArtifactBase必須field欠落、domain必須field欠落、enum・型・範囲違反を検証。TDD red: schema追加前に同テストが missing schema でfailすることを確認済み。結果: pass。

検証コマンド(サンドボックスでuv cacheをrepo配下へ向けるため `UV_CACHE_DIR=.uv-cache` を付与):

- `UV_CACHE_DIR=.uv-cache uv run pytest` → 345 passed
- `UV_CACHE_DIR=.uv-cache uv run ruff check .` → All checks passed
- `UV_CACHE_DIR=.uv-cache uv run ruff format --check .` → 17 files already formatted
- `UV_CACHE_DIR=.uv-cache uv run python scripts/gen_models.py` → exit 0。`models/change_impact_spec_schema.py` / `models/test_asset_index_schema.py` を含む生成物を書き出し
- `UV_CACHE_DIR=.uv-cache uv run python scripts/gen_models.py --check` → `models` は `schemas` の再生成結果と一致

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: [learning-log: 出力契約schemaの必須度は最初のproducerのPhase能力と突き合わせて決める](../../knowledge/learning-log.md)
