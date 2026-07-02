---
task_id: T-003
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-001, T-002]
---

# T-003: ArtifactBase JSON Schema定義

## 目的

全artifact schemaが継承する共通契約(ArtifactBase)を定義する。WS-Aの他schemaタスクすべての前提。

## 参照

- 計画: §3 WS-A
- North Star: §6.1(共通必須field一覧と継承方式)
- `schemas/README.md`(命名・継承ルール)
- 申し送り: datamodel-code-generator生成コマンド+CI diff検証の配線はT-002から本タスクへ申し送り([learning-log 2026-07-02 process-learningエントリ](../../knowledge/learning-log.md)参照)

## DoD

- [x] `schemas/artifact-base.schema.json` が存在し、§6.1に列挙された共通必須fieldすべてを必須として定義している(schemaの `required` 配列と§6.1の列挙との一致をレビューで確認。field一覧はここに複製しない: AGENTS.md変更ルール2)
- [x] schema自体がJSON Schema meta-schemaに対してvalid(テストで検証)
- [x] 有効なサンプルinstanceがpassし、必須field欠落サンプルがfailするテストがある

## 検証方法・根拠

### 追加/変更ファイル

- `schemas/artifact-base.schema.json`(正本。draft 2020-12、semver 0.1.0)
- `tests/test_artifact_base_schema.py`(46件)/ `tests/test_gen_models.py`(24件)— TDD(RED→GREEN)で作成
- `scripts/gen_models.py`(schema→Pydantic生成CLI、`--check` でdiff検証)+ 生成物 `models/artifact_base.py`(T-002からの申し送り)(注: T-004でディレクトリ一括生成へ移行し、生成物は `models/artifact_base_schema.py` へ改名。理由は[learning-log](../../knowledge/learning-log.md)参照)
- `.github/workflows/ci.yml`(CI初配線: test / lint / format / _index差分 / 生成モデル差分)
- `AGENTS.md`(構成マップに `models/` 追加、コマンド表に生成・差分検証を追記)、`schemas/README.md`($id・semver・再生成ルール追記)、`pyproject.toml`(ruffから生成物 `models/` を除外)

### DoD 1: required と§6.1の列挙の一致(レビュー)

§6.1実装注記の共通必須field 10個(artifact_id / artifact_type / version / source_refs / created_by / confidence / status / requires_human_review / trace_id / created_at)と schema の `required` 配列が一致することを目視レビューで確認。加えて `test_required_matches_section_6_1_field_list` が期待field集合との完全一致を検証する(T-001の学び「空の required は何も検証しない」への守り。期待値はテストにハードコード)。

### DoD 2・3: テスト実行結果

```text
$ uv run pytest
85 passed   # 内訳: schema契約46件 + 生成配線・CLI 24件 + 既存(_index)15件

# DoD 2: meta-schema検証 = test_schema_is_valid_against_draft_2020_12_metaschema
# DoD 3: 有効サンプル = test_valid_sample_passes / examples埋め込み分 / status全4値 / semver・confidence境界
#        欠落fail = test_missing_required_field_fails(10 field分parametrize)+ created_by子field 3件
# 追加: 空source_refsのreject(minItems: 1、ADR-0002)/ enum外status / 範囲外confidence / 非semver
```

### 申し送り(T-002→T-003): 生成コマンド+CI diff検証の配線

```text
$ uv run python scripts/gen_models.py
wrote: models/artifact_base.py          # 決定的出力(--disable-timestamp / formatter固定 / headerに do not edit)

$ uv run python scripts/gen_models.py --check
ok: models は schemas の再生成結果と一致 (exit 0)
# 手編集でtamperした場合に stale 検出で exit 1 になることも確認(missing / orphan もテストで実証)
```

生成モデルがschema埋め込みexampleを受理し、空source_refsをrejectすることもテストで確認(`tests/test_gen_models.py::TestGeneratedPydanticModel`)。CIは `.github/workflows/ci.yml` がpush(main)/PRで `--check` 2種とtest/lint/formatを実行する。

### code review(python-reviewer)と修正

- **HIGH: 生成モデルの `source_refs` がitem制約(minLength)により `RootModel` にラップされ、素の `str` として扱えない** → item側 `minLength` をschemaから除去(§6.1・ADR-0002はitem制約を要求しておらず、`minItems: 1` は維持)。regressionテスト `test_source_refs_items_are_plain_strings` をRED確認後に修正し、`source_refs: list[str]` になることを確認。`--collapse-root-models` / `--use-annotated` では解消しないことも検証済み
- **LOW: datamodel-code-generatorのバージョン範囲が広くbyte-diff検証と相性が悪い** → `>=0.66.3,<0.67` に narrowing(決定性の実保証はuv.lockである旨をコメント化)
- **LOW: CI workflowに `permissions` ブロックが無い** → `permissions: contents: read` を追加(least privilege)

### 徹底レビュー(オーナー指示、3視点並列: docs整合性 / プロセス遵守 / コード二次)と追加修正

プロセス監査は重大違反なし(変更ルール1〜6・redaction・スコープ規律すべて適合判定)。検出された指摘(CRITICAL 0 / HIGH 1 / MEDIUM 5 / LOW 3)への対応:

- **HIGH: `created_at` のセマンティクスが正本と生成モデルで非対称**(naive datetimeが生JSON検証では通り、生成モデルのAwareDatetimeでは拒否される。契約意図が未記録・未テスト)→ schema descriptionに「timezone必須が契約意図。生JSON側のformat強制はT-008で決定」と明文化し、両側に契約テストを追加(`test_naive_created_at_passes_raw_json_validation` / `test_created_at_without_timezone_is_rejected`)
- **MEDIUM: `models` importがtests/__init__.pyとimport-modeに暗黙依存** → pytest `pythonpath` に `"."` を明示。`--import-mode=importlib` でも85件全passを確認
- **MEDIUM: schemaファイル名衝突(a-b/a_b→同一module)で黙って後勝ち上書き** → `_module_mapping` で衝突時fail-fast(TDD: `test_colliding_module_names_fail_fast` のRED確認→実装)
- **MEDIUM: CLIのexit-code契約(0/1/2)が未テスト** → `TestCli` 4件を追加(check一致0 / drift1 / schemas欠落2 / 生成モード0)
- **MEDIUM: AGENTS.mdの `_index差分検証(CI用)` が生成翌日以降false driftするコマンドのまま** → `--generated-on` 付きに修正し注記を追加
- **MEDIUM: ADR-0002本文が「配線=T-002」のまま** → 事実補正の追記をADRに追加(Decision自体は不変)
- **LOW: examplesテストのvacuous pass / CI concurrency無し / format検証行の欠落** → いずれも対応
- **T-008へ申し送り2件**(learning-log記録+T-008参照節に追記): `package = false` 構成での `models/` ランタイムimport制約、生JSON側の `format` 強制判断

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見:
  - learning-log: [決定的diff検証と「生成日」の扱い(CI初配線の学び)](../../knowledge/learning-log.md)、[array item制約による生成モデルのRootModel化(T-004〜T-007への注意)](../../knowledge/learning-log.md)、[package=false構成でのmodels/ランタイムimport制約(T-008への申し送り)](../../knowledge/learning-log.md)(いずれも2026-07-02, process-learning)
  - decisions: 新規ADRなし(draft 2020-12・minItems: 1・単方向生成はADR-0002の決定に従った。$id等の表現詳細は `schemas/README.md` に規約として記載)
  - domain: なし
