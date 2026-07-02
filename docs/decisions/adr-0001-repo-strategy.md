# ADR-0001: リポジトリ戦略とskillsディレクトリ命名

- status: accepted
- date: 2026-07-02

## Context

North Star(docs/qa-agent-strategy.md)の実装にあたり、(1) 実装コードを本リポジトリ(veridia)に同居させるか、(2) skill packageのディレクトリ名を決める必要があった。§5.3のTest Asset Intelligenceは対象プロダクトrepoを跨いでindexするため、multi-repo構成も選択肢だった。また`skills/`(§7.1のQAプラットフォーム実行資産)と`.claude/skills/`(開発用エージェント拡張)の名前空間衝突の懸念があった。

## Decision

1. **monorepoとする。** 戦略・計画・ナレッジ・実装(schemas/ qa-skills/ policies/)をveridiaに集約する。
2. **skill packageディレクトリは`qa-skills/`とする**(2026-07-02改訂。当初は§7.1の規定通り`skills/`としたが、同日中にオーナー自身が`.claude/skills/`と混同したため、Consequencesに記載した再検討条件が成立し改名した)。**これはNorth Star §7.1のディレクトリ名からの意図的な逸脱である。** §7.1のパッケージ内部構造(SKILL.md、manifest、schema、validators、evals、changelog)は維持する。

## Consequences

- 個人開発・初期フェーズでは参照・変更が1箇所で完結し、エージェントの作業効率が最も高い
- 対象プロダクトが複数になった場合や、プラットフォームを独立配布する場合は、本ADRをsupersedeして分割を再検討する
- ~~`skills/`の名前空間はディレクトリ名では区別されないため、AGENTS.mdの注意書きが唯一の防御になる。混同事故が起きた場合は改名を再検討する~~ → 実際に混同が発生したため`qa-skills/`へ改名し、名前空間衝突を構造で解消した(Decision 2改訂)。トレードオフ: 混同の繰り返しリスク(静かな事故)より、記録された1回の逸脱を選んだ

## 追記(2026-07-02): agent runtime選定時のbridge方針

`qa-skills/` の意味の整理: **QAプラットフォーム自身が対象プロダクトのQA実行時に使う能力パッケージ**(§7.1)であり、対象プロダクトごとの資産でも、本リポジトリを開発するエージェントの拡張(`.claude/skills/`)でもない。プロダクト固有知識はskillsに書かず `docs/domain/` → Quality KBへ置く。

agent runtime(§22で未決: OpenAI Agents SDK相当 / 自社orchestrator / Claude Agent SDK等)を選定するADRで、以下のbridge方針を適用する:

- **正本は常にトップレベル `qa-skills/`。** runtime都合でskill定義を別ディレクトリへ複製しない
- Claude Code / Claude Agent SDKをruntimeにする場合: plugin packaging(plugin rootに `skills/` を置く規約のため、packaging時に `qa-skills/` からsymlinkまたはビルドで接続する)、または選択的に `.claude/skills/` へsymlinkする
- Codexをruntimeに含める場合: `.codex/skills/` へのsymlinkで対応する(SKILL.md規約は共通)
- いずれの場合もmanifest / evals / validators(§7.1)の正本は `qa-skills/<name>/` 配下から動かさない
