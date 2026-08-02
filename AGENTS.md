# AGENTS.md — veridia 作業ガイド

QAエージェントプラットフォーム(North Star: `docs/qa-agent-strategy.md`)の実装リポジトリ。
このファイルはAIエージェント(Claude Code / Codex等)が毎セッション読む正本。`CLAUDE.md` は本ファイルへのsymlink。

## リポジトリ構成マップ

| パス | 役割 | 状態 |
|---|---|---|
| `docs/qa-agent-strategy.md` | North Star(目標アーキテクチャ)。§番号で参照する | 稼働中 |
| `docs/plan/` | 実装計画。必ず `00-overview.md` から読む | 稼働中 |
| `docs/tasks/` | 詳細タスク。1タスク=1ファイル(`README.md` 参照) | 稼働中 |
| `docs/decisions/` | ADR。設計・技術判断とNorth Starからの逸脱の記録 | 稼働中 |
| `docs/domain/` | 対象プロダクトのドメイン知識(Quality KB稼働までの仮置き) | 稼働中 |
| `docs/knowledge/` | 実運用からの学び。North Star改訂の唯一の入力 | 稼働中 |
| `docs/operations/` | 運用runbook・RACI・KPI運用(Phase 1以降に整備) | 予定地 |
| `docs/archive/` | 旧版・レビュー文書 | - |
| `schemas/` | Artifact JSON Schema(North Star §6)。ArtifactBase + 各spec。**正本**(ADR-0002) | 稼働中 |
| `qa-skills/` | QAプラットフォームのskill package(North Star §7.1) | Phase 0で着手 |
| `policies/` | GatePolicy等のversioned config(North Star §17) | Phase 0で着手 |
| `artifact_validator/` | Artifact JSON Schemaのruntime検証lib/CLI。**2つのschema familyを扱う**: veridia契約(`schemas/`、`artifact_type` でルーティング)と sqk-core契約(`vendor/sqk-core/schemas/`、`schema_ref` でルーティング。[ADR-0007](docs/decisions/adr-0007-sqk-core-contract-consumption.md)) | 稼働中 |
| `skill_runner/` | sqk-core skillの隔離実行境界(LLMClient / SkillRunner)。[ADR-0005](docs/decisions/adr-0005-llm-skill-execution.md) / [ADR-0007](docs/decisions/adr-0007-sqk-core-contract-consumption.md) | 稼働中 |
| `run_store/` | sqk-core skill実行の監査ラッパー(RunRecord)生成と保存([ADR-0007](docs/decisions/adr-0007-sqk-core-contract-consumption.md)) | 稼働中 |
| `gate_evaluator/` | `policies/gate-policy.yaml` を読みrunを評価してGateDecision(§6.24)を出す。現在の実装gateは `source_grounding` のみで、残りは `inconclusive`(T-057) | 稼働中 |
| `source_connector/` | 対象repoのcommit rangeからdiffと変更ファイルを取得するW1入力境界(§5.1)。対象はコードではなく環境変数で指定する(T-026) | 稼働中 |
| `evidence_store/` | ExecutionEvidenceのmetadata/blob保存adapter | 稼働中 |
| `trace_store/` | redacted trace recordの保存adapter | 稼働中 |
| `trace_ids/` | run_id / trace_id / span_id生成 | 稼働中 |
| `tool_gateway/` | allowlist + schema検証付きtool実行境界 | 稼働中 |
| `sandbox_env/` | Phase 0 process sandbox lifecycle / seed / clock | 稼働中 |
| `sandbox_runner/` | sandbox実行とExecutionEvidence保存 | 稼働中 |
| `test_asset_index_generator/` | TestAssetIndex候補生成CLI | 稼働中 |
| `change_impact_generator/` | ChangeImpactSpec候補生成CLI | 稼働中 |
| `scripts/` | 生成・整合性チェック用repo-local tooling | 稼働中 |
| `tests/` | pytestによるcontract / regression test | 稼働中 |
| `vendor/sqk-core/` | 品質知識・skill blueprintの正典 [sqk-core](https://github.com/rymetry/sqk-core) をSHA固定で取り込むsubmodule。**手編集禁止**(改善はsqk-coreへIssue/PRで還流。[ADR-0006](docs/decisions/adr-0006-sqk-core-integration-method.md) / [統合方針](docs/plan/sqk-core-integration.md))。**テストプロセス成果物の契約はここが正本**であり、veridiaは再定義しない([ADR-0007](docs/decisions/adr-0007-sqk-core-contract-consumption.md))。テストがこのsubmoduleに依存するため、CIでも取得する | 稼働中 |
| `.claude/` | このリポジトリでの開発用エージェント設定。`.claude/skills` は `vendor/sqk-core/skills` へのsymlink | - |

**注意(名前空間):** `qa-skills/` はQAプラットフォームが実行時に使うskill package(§7.1)。`.claude/skills/`(このリポジトリを開発するエージェント自身の拡張)とは別物(ADR-0001参照。§7.1の `skills/` から改名した逸脱の記録あり)。sqk-coreの16スキルは現在この `.claude/skills/` レーンでのみ消費している。`qa-skills/` へのmappingはPhase 1のskill実装時に判断する([統合方針 §3](docs/plan/sqk-core-integration.md))。

## 変更ルール(必読)

1. **North Starは机上の推敲で改訂しない。** 改訂は実運用の学びがある場合のみ。手順: `docs/knowledge/learning-log.md` に `northstar-proposal` として起票 → 人間の承認 → 版数を文書内で更新 → 旧版を `docs/archive/` へ。
2. **North Starの内容を計画・タスクへ複製しない。** §番号で参照する。複製は改訂時に必ず乖離する。
3. **statusの正本は各タスクファイルのfrontmatterのみ。** `_index.md` は集約ビュー(再生成可能)、`00-overview.md` はPhaseレベルのstatusのみを持つ。同じstatusを2箇所に書かない。
4. **Redaction必須。** `docs/` 配下に secret / PII / 本番データの生値を書かない(North Star §15.4準拠)。incident・実運用の記録はマスキングしてから書く。
5. **North Starからの逸脱はADRを先に書く。** `docs/decisions/` に記録してから実施する。
6. **Phase完了はタスク消化ではなく計画mdの完了条件チェックリストで判定する。** 各項目に根拠(タスク・evidence)をリンクする。

## 作業フロー(タスク実行時)

1. `docs/tasks/<phase>/T-xxx.md` を読む → frontmatterの `plan_ref` が指す計画節を読む → 必要ならNorth Starの該当§を読む
2. 実装・検証する(タスクのDoDを満たすことを確認する)
3. タスクfrontmatterの `status` を更新する
4. 作業中に得た知見を記録してから完了とする:
   - 対象プロダクトの業務知識 → `docs/domain/`
   - 運用・プロセスの学び、gate較正の気づき → `docs/knowledge/learning-log.md`
   - 設計判断 → `docs/decisions/`
5. `docs/tasks/<phase>/_index.md` を再生成する

## 実装規約

スタック(ADR-0002 / T-002で確定):

- 言語: Python 3.12+(開発は `.python-version` で 3.12 に固定)
- パッケージ/環境/ツール管理: **uv**(依存・仮想環境・Pythonツールチェーンを単一ツールで管理。Poetryは非採用。理由: 各コマンドが単一で完結し、Python本体もuvが自動取得するため個人開発の初期セットアップが最短)
- schema lib: jsonschema(生JSON artifactのcontract検証)。**正本は `schemas/*.schema.json`**(ADR-0002)。Pydantic v2は依存として残るがartifact契約には使わない(ADR-0008)
- test: pytest / lint・format: ruff
- schema→Pydantic生成は行わない(ADR-0008で `models/` と生成パイプラインを廃止)。artifact契約の検証は `artifact_validator` が `schemas/*.schema.json` を直接読む
- CI: GitHub Actions(`.github/workflows/ci.yml`)。push(main)/ PRで test / lint / format / _index差分を検証する。submoduleを取得し `VERIDIA_REQUIRE_SQK=1` でsqk-core契約テストのskipを失敗に変える(ADR-0007)

コマンド(リポジトリルートで実行):

| 目的 | コマンド |
|---|---|
| 依存インストール(build相当) | `uv sync --group dev` |
| submodule取得(clone直後に1回) | `git submodule update --init --recursive` |
| test | `uv run pytest` |
| lint | `uv run ruff check .` |
| format | `uv run ruff format .` |
| format検証(CI用) | `uv run ruff format --check .` |
| _index再生成 | `uv run python scripts/regen_task_index.py docs/tasks/<phase>` |
| _index差分検証(CI用) | `uv run python scripts/regen_task_index.py docs/tasks/<phase> --check --generated-on <コミット済み_index.mdの生成日>` |

注: `_index差分検証` の `--generated-on` 既定は実行日のため、省略すると生成翌日以降は内容が最新でも日付差で不一致(false drift)になる。CIの実配線は `.github/workflows/ci.yml` 参照(コミット済み `_index.md` から生成日を抽出して渡す)。

コーディング規約: イミュータブル優先(frozen dataclass等)、関数は小さく単一責務、ファイルは焦点を絞る(多数の小ファイル)、エラーは黙殺せず文脈付き例外にする、固定値は定数化する。
