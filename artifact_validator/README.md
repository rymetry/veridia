# Artifact Validator

T-008のPhase 0 artifact validation module。ADR-0002どおり、正本は
`schemas/*.schema.json` であり、生成PydanticモデルではなくJSON Schemaを直接読む。

## Python API

```python
from artifact_validator import validate_artifact, validate_artifact_file

validate_artifact(artifact_dict)
validate_artifact_file("/tmp/artifact.json")
```

`validate_artifact()` は `artifact_type` から対応schemaを選び、`ArtifactValidationError`
でmachine-readableな `field_path` / `schema_path` / `validator` を返す。
`validate_artifact_file()` はファイル読み込み、JSON parse、top-level object確認も行う。

## CLI

```bash
uv run python -m artifact_validator /tmp/artifact.json
uv run python -m artifact_validator /tmp/artifact.json --json
```

Exit code:

- `0`: valid
- `1`: JSONは読めたがartifact schema検証に失敗
- `2`: ファイル欠落、JSON parse error、top-level objectでない入力

`--json` は検証エラー(exit 1)をJSONでstderrへ出す。入力エラー(exit 2)は通常の
`error: ...` 形式を維持する。
