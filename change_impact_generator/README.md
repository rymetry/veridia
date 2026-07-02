# ChangeImpactSpec generator

T-010のPhase 0最小generator。git unified diffを読み、`change_impact_spec`
artifact JSONを生成する。LLMは使わず、diff headerとpath規則だけで候補を作る。

```bash
uv run python -m change_impact_generator tests/fixtures/change_impact/sample.diff /tmp/change-impact-spec.json --source-ref fixture://sample-pr
uv run python -m artifact_validator /tmp/change-impact-spec.json
```

## Phase 0の候補レベル

Phase 0ではdiffに現れたファイルとpath由来のcomponent候補だけを収集する。
Requirement / Risk / APIへの意味的マッピングはPhase 1以降の対象とし、このgeneratorは
推定しない。

- `changed_files[].analysis_status`: `candidate_path_only_phase_0`。
- `changed_files[].component`: path規則からの候補。
- `impacted_requirements`: 空配列。未収集または該当なしを表す。
- `impacted_risks`: 空配列。未収集または該当なしを表す。
- `impacted_apis`: 空配列。未収集または該当なしを表す。
- `confidence`: `0.4`。candidate-levelの低confidence。
- `requires_human_review`: `true`。

## component / risk規則

component候補は決定的なpath規則で作る。

- `src/<name>/...` -> `<name>`
- `qa-skills/<name>/...` -> `qa-skills/<name>`
- その他 -> first path segment

暫定riskはpath rootから決める。`schemas` / `policies` / `artifact_validator` /
`models` はhigh、`src` / `qa-skills` / generator packageはmedium、`docs` / `tests`
はlow、未知のrootはmedium。

## 決定性

デフォルトの `created_at` は `1970-01-01T00:00:00Z` に固定する。実運用の生成時刻を
記録したい場合は `--generated-at` で明示する。IDはsource ref、生成時刻、変更file
metadataのsha256から生成する。同一diffと同一引数では同一JSONになる。
