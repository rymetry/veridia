---
task_id: T-004
epic: artifact-schema
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-003]
---

# T-004: コアspec schema定義(RequirementSpec / RiskSpec / OracleSpec)

## 目的

Phase 1のagent/skillが入出力に使うコア3 artifactのJSON Schemaを定義する。

## 参照

- 計画: §3 WS-A
- North Star: §6.3(RequirementSpec)、§6.4(RiskSpec)、§6.6(OracleSpec)

## DoD

- [x] `schemas/requirement-spec.schema.json` / `risk-spec.schema.json` / `oracle-spec.schema.json` が存在し、`allOf` でartifact-baseを継承している
- [x] 各schemaについて、有効サンプルがpassし、domain固有必須field欠落サンプルがfailするテストがある

## 検証方法・根拠

### 追加/変更ファイル

- `schemas/requirement-spec.schema.json` / `risk-spec.schema.json` / `oracle-spec.schema.json`(正本。draft 2020-12、各semver 0.1.0。`allOf` で artifact-base を継承)
- `tests/test_core_spec_schemas.py`(126件)— TDD(RED→GREEN)で作成
- `scripts/gen_models.py` + `tests/test_gen_models.py`(31件)— ディレクトリ一括生成へ移行(下記)+ 生成物 `models/`(`artifact_base_schema.py` 等4モジュール+`__init__.py` に改名・再生成)

### DoD 1: 存在とallOf継承(テストで検証)

- `test_schema_file_exists` / `test_inherits_artifact_base_via_allof`(3スキーマ×parametrize)が、ファイル存在と `allOf` に `{"$ref": "artifact-base.schema.json"}` を含むことを検証
- 継承が実際に強制されることも検証: base必須field 10個の欠落fail(×3スキーマ=30件)、空`source_refs`のreject(ADR-0002)、`artifact_type` const不一致のfail

### DoD 2: 有効サンプルpass / domain必須欠落fail(テスト実行結果)

```text
$ uv run pytest
218 passed   # 内訳: コアspec契約126件 + base契約46件 + 生成配線31件 + _index 15件

# 有効サンプル: full(optional込み)/ minimal(必須のみ)/ schema埋め込みexamples の3系統×3スキーマ
# domain必須欠落fail: RequirementSpec(req_id / title / acceptance_criteria)、
#   RiskSpec(risk_id / title / severity / likelihood)、
#   OracleSpec(oracle_id / req_refs / oracle_type / signals / pass_condition)の全12 field分parametrize
# 値域: oracle_type全9種(§9.2/9.3)pass+enum外fail、severity 4段階/likelihood・detectability 3段階、
#   business_impact 4段階、空配列reject(acceptance_criteria / req_refs / signals / oracle_type / risk_refs)
# 生成モデルsmoke: examples受理+domain必須欠落reject(×3スキーマ)+signal追加fieldのround-trip保持

$ uv run ruff check . && uv run ruff format --check .   # OK
$ uv run python scripts/gen_models.py --check           # ok: models は schemas の再生成結果と一致
```

### 設計判断(North Starが値域・必須を明示しない箇所の確定。各schema descriptionにも記載)

- domain必須field: RequirementSpec=req_id/title/acceptance_criteria(§9 oracle設計の入力)、RiskSpec=risk_id/title/severity/likelihood(severity充足は§7.2 preconditionが要求)、OracleSpec=oracle_id/req_refs/oracle_type/signals/pass_condition(req_refs必須は§9.1 oracle-firstによる)。他はdraft段階で確定しないためoptional
- enum値域: oracle_type=§9.2+§9.3の9種。severity/business_impact=low|medium|high|critical(§6.4/§6.11/§8.4の用例を被覆)、likelihood/detectability=low|medium|high(criticalは尺度として不成立)
- 具象schemaは `unevaluatedProperties: false` で閉じる(typo・契約違反のfail-fast。baseは合成のため開いたまま)
- optional配列は「空にするならキー省略」(minItems: 1)で空配列の曖昧さを排除
- 子schemaで再宣言した `artifact_type`(const)は子のrequiredにも再列挙(生成モデルのOptional化防止 → learning-log)

### 付随変更: gen_models.py のディレクトリ一括生成移行

allOf外部$ref(modular reference)はdcgのファイル単位出力と両立しないため移行(詳細・付随論点は[learning-log](../../knowledge/learning-log.md)の3エントリ参照)。生成モジュール名は `<type>_schema.py` に変わり、T-003記録に改名の注記を追加。旧 `models/artifact_base.py` は削除(orphan掃除は `generate_all` が自動実行)。

### コードレビュー

python-reviewerエージェントでレビューを実施(2026-07-02)。CRITICAL相当1件(生成 `Signal` モデルがPydantic既定 `extra=ignore` で追加fieldを黙って捨てるsilent data loss)は実装中に検出・修正済み(`additionalProperties: true` 明示+round-trip regression test)。HIGH 0件。MEDIUM 1件($ref解決にRegistryが必要な規約の未文書化 → `schemas/README.md` へ追記)、LOW 1件(`generate_all` のorphan削除とcopyの順序 → copy先行へ入れ替え)を反映し、全チェック再GREENを確認。

徹底レビュー(2次: 敵対的コードレビュー+ドキュメント/プロセス監査の2エージェント並列、2026-07-02)で追加7件を検出し全件反映:
- HIGH: `oracle_type` の `uniqueItems` が生成モデルで非強制(生JSONのみreject)→ 挙動固定のregression test+schema description・learning-logへ明記
- MEDIUM: `models/` がファイル時の `FileExistsError` 未捕捉 → `main()` で `OSError` を捕捉しexit 2へ正規化(テスト追加)/ dcg失敗時にstdoutを握り潰す → エラーメッセージへ含める(テスト追加)/ `docs/plan/phase-0-foundation.md` のPhaseレベルstatus複製行の矛盾(T-004以前からの既存問題)→ 参照のみ化
- LOW: `schemas/README.md` のadditionalProperties規則へ合成用base例外を明文化 / `referencing` を明示依存へ昇格 / dot由来モジュール名衝突のテスト追加

反映後の再検証: `uv run pytest` 218 passed / ruff check・format OK / `gen_models.py --check` 一致 / `_index` 差分検証 OK。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見:
  - [learning-log: allOf外部$refとdcgディレクトリ一括生成](../../knowledge/learning-log.md)(2026-07-02、T-004)
  - [learning-log: 開いたobjectのadditionalProperties明示(silent data loss防止)](../../knowledge/learning-log.md)(2026-07-02、T-005〜T-007への注意)
  - [learning-log: const再宣言fieldのrequired再列挙](../../knowledge/learning-log.md)(2026-07-02、T-005〜T-007への注意)
  - domain / decisions: なし(North Starからの逸脱なし。値域等の確定は上記「設計判断」とschema descriptionに記載)
