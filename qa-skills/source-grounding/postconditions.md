# Postconditions

- 出力は handoff envelope 1件であり、`artifacts` は `SourceMap` 1件。
- `SourceMap` が `veridia://schemas/source-map.schema.json` を満たす(`artifact_validator` が検証する)。
- `extracted_items` の各 `span` が、入力の `diff_text` に実在する path と行範囲を指す。
- `trust_level` は取り込み層の値で上書きされている(このskillの出力値は採用されない。ADR-0009)。
- `status` は `draft`。人間レビュー前の候補である(計画§7)。
