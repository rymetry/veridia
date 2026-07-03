# Tool Gateway

T-015のPhase 0最小Tool Gateway。tool呼び出しを `ToolGateway.execute()` 経由に集約し、allowlistとJSON Schema validationだけを実施する。

## 構成

```text
tool_gateway/
  __init__.py       # 公開API
  builtin_tools.py  # Phase 0のread-only repo tool
  errors.py         # 専用エラー型
  gateway.py        # allowlist、input/output validation、実行境界
  registry.py       # tool名 -> schema/callable のregistry
  validation.py     # jsonschemaベースのvalidation helper
```

## 使い方

```python
from tool_gateway import ToolGateway, create_default_registry

gateway = ToolGateway(
    registry=create_default_registry("."),
    allowlist=frozenset({"repo.read_text_file"}),
)
result = gateway.execute("repo.read_text_file", {"path": "AGENTS.md"})
```

`ToolDefinition` は `name`、`input_schema`、`output_schema`、`handler` を持つ。`handler` はJSON object相当の `Mapping[str, Any]` を受け取り、JSON object相当の結果を返す。Gatewayは実行前にinput schema、実行後にoutput schemaを検証する。

T-016のaudit logは `ToolGateway.execute(tool_name, payload)` の呼び出し境界をフックする想定。T-015ではTrace Storeへの保存、trace_id付与、redactionは行わない。

## 登録済みtool

- `repo.read_text_file`: repository root配下の相対パスをUTF-8 textとして読み取る。絶対パスとroot外へのpath traversalは拒否する。
- `repo.list_files`: repository root配下の相対ディレクトリからfile listを返す。`.git` 配下は列挙しない。

どちらもread-onlyで、repo外への書き込みや破壊的操作は行わない。

## Phase 0でスコープ外

North Star §5.6のうち、T-015では次を実装しない。

- AuthN/AuthZ
- Pre-execution guardrail / Post-execution guardrail
- Dry-run
- Approval
- Audit log(T-016で追加)
- Rate limit
- Test asset accessのread-only index化
- Performance tool control

T-015の責務はallowlistとinput/output schema validationの最小実装に限定する。
