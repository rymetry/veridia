---
task_id: T-015
epic: tool-gateway
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-002]
---

# T-015: Tool Gateway最小版(allowlist + schema validation)

## 目的

tool呼び出しをGateway経由に強制する最小実装。§5.6の全機能表ではなく、allowlistとschema validationのみに留める(計画§6のスコープクリープ注意)。

## 参照

- 計画: §3 WS-C、§6(最小実装に留める)
- North Star: §5.6(Tool allowlist / Schema validation)

## DoD

- [ ] tool呼び出しがGateway経由で実行でき、allowlist外のtool呼び出しはrejectされる(テストで実証)
- [ ] tool input / outputがschema検証され、violation時はエラーになる(テストで実証)
- [ ] 最小のtool 1〜2種(例: repo読み取り、test実行)が登録され、正常系が動作する
- [ ] §5.6のうちPhase 0で実装しない機能(AuthN/AuthZ / guardrail / dry-run / approval / rate limit等)がREADMEにスコープ外として明記されている

## 検証方法・根拠

- Gateway経由の正常実行:
  - `tests/test_tool_gateway.py::test_executes_allowlisted_registered_tool`
  - `repo.read_text_file` を `ToolGateway.execute()` 経由で実行し、schema validation後にfile contentを返すことを確認
- allowlist外tool呼び出しのreject:
  - `tests/test_tool_gateway.py::test_rejects_tool_outside_allowlist`
  - allowlistに含まれない `repo.read_text_file` が `ToolNotAllowedError` になることを確認
- input schema violation:
  - `tests/test_tool_gateway.py::test_rejects_input_schema_violation`
  - `path` にnumberを渡すと `ToolSchemaValidationError(direction="input")` になることを確認
- output schema violation:
  - `tests/test_tool_gateway.py::test_rejects_output_schema_violation`
  - handlerがschema外のoutputを返すと `ToolSchemaValidationError(direction="output")` になることを確認
- 登録済み最小tool:
  - `tool_gateway.create_default_registry()` で `repo.read_text_file` / `repo.list_files` を登録
  - いずれもread-onlyで、repo root外へのpath traversalを拒否
- README:
  - `tool_gateway/README.md` に構成、使い方、登録tool、Phase 0で実装しない§5.6項目(AuthN/AuthZ / guardrail / dry-run / approval / rate limit / audit log(T-016)等)を記載
- 実行結果:
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run pytest` → 443 passed
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run ruff check .` → All checks passed
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run ruff format --check .` → 59 files already formatted

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
