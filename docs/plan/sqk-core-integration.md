# sqk-core 統合方針

作成日: 2026-07-07
最終改訂: 2026-08-01(sqk-core v2 正典化完了を受けた全面改訂)
status: active

## 1. 目的と分担

[sqk-core](https://github.com/rymetry/sqk-core) は品質知識とスキルblueprintの正典リポジトリ、veridiaはそれを取り込んでQA実行・判定・証跡化を行う実行系(runtime consumer)。本ファイルはveridia側の取り込み方針を定める。

```text
sqk-core
  品質知識の正典 / SKILL.md blueprint / I/O schema
        ↓ commit SHA固定のcheckout
veridia
  QAエージェント実行基盤。計画・実行・判定・証跡化で利用する
        ↓ GitHub Issue / PR
sqk-core(実実行ベースのフィードバック)
```

sqk-coreの内容をveridiaへ複製しない。SKILL.md原本をveridia固有に書き換えない(差分が必要ならveridia側adapterで吸収する)。

### 旧版からの変更点(2026-08-01)

初版(2026-07-07)は次の3点が現状と乖離していたため全面改訂した。

- **リポジトリ名**: `software-quality-knowledge-base` は削除済み。sqk-coreとして再構築されている
- **成果物の状態**: 「v3調査索引(一次情報確認・正規化が未完了)」を前提にしていたが、正典化は完了している(SKILL.md blueprint 16ユニット、I/O JSON Schema 18件、derived knowledge、domain canon)
- **待ち条件**: 「sqk-core側の実装が完了するまでveridiaでは具体実装タスクを作らない」という条件は、sqk-coreのD-012(土台先行のベース作成と再評価ループ。ROADMAP 5節の全ウェーブ完了はそのウェーブ4追記に記録)およびD-013(取り込みインターフェース確定)をもって**解除済み**

## 2. 取り込みインターフェース

**正本はsqk-coreの [`platforms/veridia/README.md`](https://github.com/rymetry/sqk-core/blob/main/platforms/veridia/README.md)**(sqk-core D-013で確定)。ここには要点のみ記す。内容を複製しない。

- **取り込み単位はリポジトリ全体のcheckoutをcommit SHAで固定すること**。`knowledge_refs` とSKILL.md本文のリンクがリポジトリ相対パスで書かれており、参照先が `docs/agent-ecosystem/` の設計文書にまで及ぶため、`skills/` 単体の抜き出しでは参照が解決できない
- sqk-coreはリリースタグを発行していない。**固定SHAの付け替えが更新**であり、スキル単位の互換性判断はfrontmatterの `version`(semver)で行う
- 取り込み面は skills / schemas / knowledge / domain canon の4種。`docs/_research/`・`docs/migration/`・sqk-coreローカルの `scripts/`・`tests/` 等は実行時の読み込み対象外
- SKILL.mdはClaude Code互換形式。Claude Code系runtimeはシンボリックリンク配置のみで発見・発火できる

## 3. 2レーン構造

sqk-coreのSKILL.md blueprintは、veridiaでは用途の異なる2つのレーンで消費する。両者を混同しない(名前空間の区別はAGENTS.mdのリポジトリ構成マップ参照)。

| | 開発エージェントレーン | runtimeレーン |
|---|---|---|
| 消費者 | veridiaを開発・QAするClaude Codeセッション | QAプラットフォーム本体(North Star §7.1) |
| 配置 | `.claude/skills` → `vendor/sqk-core/skills` のsymlink | `qa-skills/` のskill package |
| 状態 | **配線済み**(2026-08-01) | Phase 1以降 |
| 変換 | なし(SKILL.md原本をそのまま発見) | blueprint → package へのmappingが必要 |

### 3.1 開発エージェントレーン(配線済み)

sqk-coreをsubmodule `vendor/sqk-core` としてSHA固定でcheckoutし、`.claude/skills` からsymlinkで参照する。これによりveridiaを開発するエージェントセッションが16スキルを直接発見・利用できる。

```text
.claude/skills -> ../vendor/sqk-core/skills
```

固定SHA: `54e78cc7f5b5bb1fcd63a72495a530929538f3f8`(2026-08-01時点のsqk-core origin/main)

このレーンはveridiaのruntime挙動に影響しない。開発時のエージェント支援のみに使う。

注意点:

- **スキル名の衝突**: sqk-coreの `code-review` は、Claude Code組み込みの `/code-review` コマンドや他プラグインの同名スキルと名前が重なる。曖昧な場合はプラグイン接頭辞付きの名前で明示的に指定する
- **submodule未取得時**: `.claude/skills` はdangling symlinkになり、スキルは1つも発見されない(エラーにはならない)。clone直後は `git submodule update --init --recursive` を実行する(AGENTS.mdのコマンド表参照)。veridiaのCIはsubmoduleをcheckoutしないが、lint・testはvendorを対象外にしているため影響しない

### 3.2 runtimeレーン(Phase 1以降)

`qa-skills/` へのmappingは本ファイルの範囲外(方針のみ記す)。**対応表はPhase 1の各skill実装タスクに着手する時点で作る**。先に机上で対応表を確定させない。

Phase 1タスクとsqk-coreスキルの対応候補(暫定。実装時に検証して確定させる):

| Phase 1タスク | sqk-coreスキル(候補) |
|---|---|
| [T-030 `requirement-risk-analysis`](../tasks/phase-1/T-030-requirement-risk-analysis-skill.md) | `risk-analysis` / `test-requirement-analysis` |
| [T-032 `oracle-selection`](../tasks/phase-1/T-032-oracle-selection-skill.md) | `test-design-implementation` / `test-architecture-design` |
| [T-050 `failure-triage`](../tasks/phase-1/T-050-failure-triage-skill.md) | `test-execution-support` / `defect-analysis-rca` |
| [T-053 `release-readiness-reporting`](../tasks/phase-1/T-053-release-readiness-reporting-skill.md) | `quality-gate-release-judgment` |

mapping時の制約(sqk-core D-012の実行境界):

- sqk-coreのスキルはruntime-neutralなblueprintであり、テスト実行・探索実行・証跡収集はveridia側が担う
- veridiaのruntime artifact / evidence / gate mappingをスキルの出力契約へ混ぜない。mappingはveridia側のadapterレイヤーで持つ

## 4. 更新運用

固定SHAの付け替えが更新にあたる。手順:

1. `vendor/sqk-core` を目標SHAへ進め、submoduleの参照を更新する
2. 取り込み先checkoutで `uv run scripts/check.py` がgreenであることを確認する(sqk-coreローカルの検証機構であり取り込み面には含まれない。SHA更新時の健全性確認としてのみ使う)
3. 利用中スキルのfrontmatter `version` の差分を確認する(semver。majorが上がっていれば利用側の見直しが必要)
4. 本ファイル §3.1 の固定SHA記載を更新する

## 5. フィードバック経路

実利用で見つけた所見(出力エンベロープのschema不整合、SKILL手順・文言の曖昧さ、`knowledge_refs` の不足・誤り、ゲート判定の齟齬など)は、**sqk-coreのGitHub Issue / PRへ起票する**。veridia側で原本を書き換えて済ませない。

起票時に最低限含めるもの:

- 対象スキルの `name` と `version`、および固定していたcommit SHA
- 実行環境の要約(runtime種別、`capabilities` の解決状況)
- 事象の区分と再現材料(エンベロープ抜粋等)

**対象プロダクト固有の非公開データ(product spec・品質基準・欠陥履歴)をpublic repoであるsqk-coreへ持ち込まない**(AGENTS.md変更ルール4のredaction原則と同趣旨)。持ち込めない情報が再現に必要な場合は、マスキングした最小再現に加工してから起票する。

## 6. 現時点でやらないこと

- sqk-coreの知識本文をveridiaへ複製しない(参照はsubmodule経由に限る)
- SKILL.md原本をveridia固有に書き換えない
- runtimeレーンの実装(`qa-skills/` へのmapping)を、Phase 1の該当skill実装タスクに着手する前に先行させない
- 未確定のsqk-core成果物へruntime依存を作らない。runtime依存は最小のconsumer pathから始める
- ドメイン固有知識を汎用platform coreへ直書きしない
- CRUD/業務アプリ以外の知識をPhase 1の主線へ混ぜ込まない

## 7. 未決事項

| ID | 事項 | status / 決定タイミング |
|---|---|---|
| OQ-KB-1 | 最初の取り込み対象 | **決定済み(2026-08-01)**: sqk-core D-013に従いリポジトリ全体をcheckoutする。個別成果物の選別はしない |
| OQ-KB-2 | 連携方式(submodule / package / vendored copy / local path) | **決定済み(2026-08-01)**: git submoduleでSHA固定。[ADR-0006](../decisions/adr-0006-sqk-core-integration-method.md) |
| OQ-KB-3 | SHA更新時の互換性チェック | 方針決定済み(2026-08-01): §4の手順。自動化の要否はPhase 1のruntimeレーン着手時に判断する |
| OQ-KB-4 | 初回consumer対象の `quality_profile` | Phase 2以降の計画時 |
| OQ-KB-5 | generic platform contract と profile-specific adapter の境界 | **決定済み(2026-08-02)**: 境界は「契約 vs 契約の扱い」に引く。テストプロセス成果物(工程0〜8)の契約はsqk-coreを正本として直接消費し、adapter層は作らない。veridiaが定義するのは実行系固有のもの(ExecutionEvidence / GateDecision / GatePolicy / RunRecord)に限る。[ADR-0007](../decisions/adr-0007-sqk-core-contract-consumption.md) |
