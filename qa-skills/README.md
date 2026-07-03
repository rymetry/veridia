# qa-skills/ — QAプラットフォーム skill package

North Star §7.1のskill package構造に従う実行資産を置く。Phase 0でregistry規約を定め、Phase 1で最初のskill群を実装する。

ディレクトリ名は§7.1の `skills/` から改名した意図的な逸脱(経緯とruntime接続のbridge方針はADR-0001参照)。

## ルール

- 1 skill = 1ディレクトリ。内部構造は§7.1の規定(SKILL.md、manifest.yaml、input/output schema、validators、scripts、evals、changelog)に従う
- manifestのschema正本は `qa-skills/manifest.schema.json`。skill manifestはartifactではないため `schemas/*.schema.json` には置かず、Pydanticモデル生成対象にも含めない
- manifestの必須項目は `name` / `version` / `owner` / `description` / `inputs` / `outputs`。§7.2の例にある `trigger` / `preconditions` / `quality_gates` / `validators` / `failure_modes` は、Phase 0-1で未確定になり得るためoptional(書く場合はschemaで型・値を検証する)
- registry metadataは§28.2「残すもの」に従う。`name` はregistryの `skill_id`、`version` / `owner` は同名metadataの基礎値、`inputs` / `outputs` は `input.schema.json` / `output.schema.json` との整合確認に使う
- skill変更時はskill eval必須(§27.1)
- **`.claude/skills/`(開発用エージェント拡張)とは別物**。ここにあるのはQAプラットフォームが対象プロダクトをQAする際に実行する能力パッケージであり、このリポジトリを開発するためのスキルではない

## 新規skill作成手順

1. `qa-skills/_template/` を `qa-skills/<skill-id>/` にコピーする。`<skill-id>` はmanifest `name` と同じkebab-caseにする。
2. `manifest.yaml` の `name` / `version` / `owner` / `description` / `inputs` / `outputs` を更新する。`trigger` 等のoptional fieldも書ける段階のものだけ更新する。
3. `SKILL.md` / `preconditions.md` / `postconditions.md` / `failure_modes.md` をそのskill固有の手順・条件へ置き換える。
4. `input.schema.json` / `output.schema.json` をそのskillの入出力契約に置き換える。skill固有schemaなので `schemas/` ではなくskill package内に置く。
5. `validators/` と `scripts/` のstubを実装し、`evals/` にpositive / negative / regression caseを追加する。exampleはredaction済みの最小例だけを `examples/` に置く。
6. `tests/test_skill_manifest_schema.py` と同じ流儀で、manifestとpackage構造のvalidationをpytestで実証する。
