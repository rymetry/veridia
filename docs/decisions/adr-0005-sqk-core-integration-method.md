# ADR-0005: sqk-core の連携方式(git submodule による SHA 固定)

- status: accepted
- date: 2026-08-01

## Context(何を決める必要があったか)

品質知識・スキルblueprintの正典である [sqk-core](https://github.com/rymetry/sqk-core) をveridiaへ取り込むにあたり、連携方式が未決だった([sqk-core-integration.md](../plan/sqk-core-integration.md) の OQ-KB-2)。

前提条件:

- sqk-core D-013 が取り込み単位を「**リポジトリ全体のcheckoutをcommit SHAで固定**」と定めている。`knowledge_refs` とSKILL.md本文のリンクがリポジトリ相対パスで書かれ、参照先が `docs/agent-ecosystem/` の設計文書にまで及ぶため、`skills/` 単体の抜き出しでは参照が解決できない
- sqk-coreはリリースタグを発行していない。バージョン固定の手段はcommit SHAのみ
- veridiaの変更ルール2(North Starの内容を計画・タスクへ複製しない)と同じ趣旨で、外部正典の内容もveridiaへ複製しない方針

## Decision(何を決めたか)

**git submodule として `vendor/sqk-core` に配置し、commit SHA で固定する。**

初回固定SHA: `54e78cc7f5b5bb1fcd63a72495a530929538f3f8`(2026-08-01時点のsqk-core origin/main)

開発エージェントレーンの配線として `.claude/skills -> ../vendor/sqk-core/skills` のシンボリックリンクを張る。これはsqk-core自身の `platforms/claude-code` が採るアダプター思想と同一で、原本を複製しない。

### 却下した代替案

| 代替案 | 却下理由 |
|---|---|
| vendored copy(`skills/` 等をveridiaへコピー) | 内容の複製にあたり、「正典を複製しない」原則に反する。更新のたびに乖離が発生する。ディレクトリ単位の抜き出しは `knowledge_refs` の参照が切れる(D-013) |
| ローカルパス参照(`~/Dev/.../sqk-core` を直接指す) | 再現性がない。checkout位置と版が環境ごとに異なり、CI・他マシン・エージェントセッションで同じ状態を保証できない |
| package化(PyPI等への公開・依存追加) | sqk-core側にpackaging・リリース運用の負担を課す。sqk-coreはタグすら発行しておらず、現状の運用と乖離する。取り込むのはコードではなくMarkdown/JSONの知識成果物であり、packageの利点が薄い |

## Consequences(トレードオフ、影響)

- **利点**: SHAが `.gitmodules` とindexに記録されるため、どの版を取り込んでいるかがveridiaの履歴に残る。更新はSHAの付け替えのみで、差分がPRで可視化される。原本の複製が発生しない
- **コスト**: clone時に `--recurse-submodules`(または `git submodule update --init`)が必要になる。CIで取り込み先の内容を使う場合は同様の配慮が要る。現時点ではveridiaのテスト・CIはsubmoduleに依存しないため、CI設定の変更は行わない
- **更新運用**: SHA付け替え時に、取り込み先checkoutで `uv run scripts/check.py` がgreenであること、および利用中スキルのfrontmatter `version` の差分を確認する(OQ-KB-3。手順は [sqk-core-integration.md §4](../plan/sqk-core-integration.md))
- **スコープ**: 本ADRが配線するのは開発エージェントレーンのみ。`qa-skills/` へのruntime mappingは別途Phase 1のskill実装タスクで判断する(OQ-KB-5)。veridiaのruntime挙動には影響しない
