---
task_id: T-007
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-003]
---

# T-007: 基盤spec schema定義(QualityAnalyticsSnapshot / ReleaseReadinessReport)

## 目的

Reporting Foundationの2 artifactのJSON Schemaを定義する。計画§2完了条件「ReleaseReadinessReportのschemaがvalidationを通る」をカバーする。

## 参照

- 計画: §2 完了条件、§3 WS-A
- North Star: §6.17(QualityAnalyticsSnapshot)、§6.18(ReleaseReadinessReport)

## DoD

- [x] `schemas/quality-analytics-snapshot.schema.json` / `release-readiness-report.schema.json` が存在し、`allOf` でartifact-baseを継承している
- [x] QualityAnalyticsSnapshotがcoverage / execution / evidence / costを集約できる(サンプルinstanceで確認)
- [x] ReleaseReadinessReportがpass/warn/block・理由・evidence_refsを表現でき、有効サンプルinstanceがschema validationを通る(テストで実証。計画§2完了条件)
- [x] 各schemaについて、不正サンプルがfailするテストがある

## 検証方法・根拠

- DoD 1: `schemas/quality-analytics-snapshot.schema.json` / `schemas/release-readiness-report.schema.json` を追加し、`tests/test_reporting_schemas.py` の `test_inherits_artifact_base_via_allof` で `artifact-base.schema.json` の `allOf` 継承を検証。結果: pass。
- DoD 2: QualityAnalyticsSnapshotの§6.17相当サンプルをschema `examples` と `make_quality_analytics_snapshot_instance()` に置き、coverage / execution / evidence / costの集約bucketを保持できることを検証。Phase 0にはproducerが無いため、bucket自体はdomain必須、個別metricはoptionalまたはnull許容とした。`test_quality_analytics_snapshot_unmeasured_optional_metrics_pass` で未収集metricのdraftがpassすること、coverage比率・execution件数・evidence_refs型・cost値の不正サンプルがfailすることを確認。結果: pass。
- DoD 3: ReleaseReadinessReportの§6.18相当サンプルをschema `examples` と `make_release_readiness_report_instance()` に置き、`decision_recommendation` の pass / warn / block、理由配列、`evidence_refs` を表現できることを検証。Phase 0にはproducerが無いため、判定・理由配列・evidence_refsのキー存在をdomain必須とし、理由配列とevidence_refsは空配列を許す。`test_release_readiness_report_all_decisions_pass` で3判定がpassすること、未知の判定・readiness_score範囲外・理由本文欠落・evidence_refs型違反がfailすることを確認。結果: pass。
- DoD 4: `tests/test_reporting_schemas.py` で有効サンプル、schema埋め込みexample、ArtifactBase必須field欠落、domain必須field欠落、enum・型・範囲違反を検証。TDD red: schema追加前に同テストが missing schema でfailすることを確認済み。結果: pass。

必須度の判断:

- ArtifactBaseの共通必須fieldと `source_refs minItems: 1` は継承で強制する。
- 子schema側では、生成PydanticモデルがOptional化しないよう `artifact_type` をrequiredへ再列挙する。
- QualityAnalyticsSnapshotはDoDの4 bucket(coverage / execution / evidence / cost)を必須にし、bucket内部のmetricはPhase 0 producer未定義のため必須化しない。
- ReleaseReadinessReportはT-007の契約対象である判定・理由・evidence_refsを必須にし、pass判定や未収集draftでrefや理由の捏造を要求しないよう配列は空を許す。

検証コマンド(uv cacheをrepo外へ向けるため `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache` を付与):

- `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest` → 407 passed
- `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff check .` → All checks passed
- `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff format --check .` → 18 files already formatted
- `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python scripts/gen_models.py` → exit 0。`models/quality_analytics_snapshot_schema.py` / `models/release_readiness_report_schema.py` を含む生成物を書き出し
- `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run python scripts/gen_models.py --check` → `models` は `schemas` の再生成結果と一致

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし(既存の [learning-log: 出力契約schemaの必須度は最初のproducerのPhase能力と突き合わせて決める](../../knowledge/learning-log.md) を判断根拠として参照)
