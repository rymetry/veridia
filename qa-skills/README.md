# qa-skills/ — QAプラットフォーム skill package

North Star §7.1のskill package構造に従う実行資産を置く。Phase 0でregistry規約を定め、Phase 1で最初のskill群を実装する。

ディレクトリ名は§7.1の `skills/` から改名した意図的な逸脱(経緯とruntime接続のbridge方針はADR-0001参照)。

## ルール

- 1 skill = 1ディレクトリ。内部構造は§7.1の規定(SKILL.md、manifest.yaml、input/output schema、validators、scripts、evals、changelog)に従う
- manifestの必須項目は§7.2、registry metadataは§28.2「残すもの」に従う
- skill変更時はskill eval必須(§27.1)
- **`.claude/skills/`(開発用エージェント拡張)とは別物**。ここにあるのはQAプラットフォームが対象プロダクトをQAする際に実行する能力パッケージであり、このリポジトリを開発するためのスキルではない
