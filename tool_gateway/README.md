# Tool Gateway

T-015/T-016のPhase 0最小Tool Gateway。tool呼び出しを `ToolGateway.execute()` 経由に集約し、allowlistとJSON Schema validationを実施する。監査ログが必要な実行では `AuditedToolGateway` でこの境界をwrapし、Trace Storeへredactedなtool call recordを保存する。

## 構成

```text
tool_gateway/
  __init__.py       # 公開API
  audit.py          # ToolGateway.execute()のaudit log wrapper
  builtin_tools.py  # Phase 0のread-only repo tool
  errors.py         # 専用エラー型
  gateway.py        # allowlist、input/output validation、実行境界
  redaction.py      # tool argsのsecret-pattern redaction
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

## Audit log付き実行(T-016)

```python
from tool_gateway import AuditedToolGateway, ToolGateway, create_default_registry
from trace_ids import IdFactory
from trace_store import TraceStore

id_factory = IdFactory()
parent_context = id_factory.new_trace_context()
gateway = ToolGateway(
    registry=create_default_registry("."),
    allowlist=frozenset({"repo.read_text_file"}),
)
audited_gateway = AuditedToolGateway(
    gateway=gateway,
    trace_store=TraceStore.open("/tmp/veridia-trace"),
    parent_context=parent_context,
    id_factory=id_factory,
)

result = audited_gateway.execute("repo.read_text_file", {"path": "AGENTS.md"})
```

`AuditedToolGateway.execute(tool_name, payload)` は、呼び出しごとに `parent_context` を親にしたchild `TraceContext` を作成し、実行後に `event_type="tool_call"` のTrace Store recordを保存する。複数回のtool callは同じ `run_id` / `trace_id` を共有し、各recordの `span_id` と `parent_span_id` で親子関係を表す。

保存する主なfield:

- `run_id` / `trace_id` / `span_id` / `parent_span_id`
- `sequence`
- `event_type="tool_call"`
- `name`
- `status`: `success` または `error`
- `started_at` / `ended_at` / `latency_ms`
- `redacted_args`
- `result_summary` または `error_summary`

allowlist reject、input/output schema violation、handler例外のいずれも `status="error"` のrecordを保存してから、元の例外を再送出する。

### Redaction方針

Trace Storeにはraw args / raw resultを保存しない。`redacted_args` は `redact_tool_args()` で作成する。Phase 0の最小ルールとして、key名に `token` / `secret` / `password` / `api_key` / `authorization` / `auth` を含む値を `"<redacted>"` に置き換える。dict/list内のnested valueも再帰的に処理する。`result_summary` は結果objectのkey一覧とfield数だけを保存し、raw result payloadは保存しない。

## 登録済みtool

- `repo.read_text_file`: repository root配下の相対パスをUTF-8 textとして読み取る。絶対パスとroot外へのpath traversalは拒否する。
- `repo.list_files`: repository root配下の相対ディレクトリからfile listを返す。`.git` 配下は列挙しない。

どちらもread-onlyで、repo外への書き込みや破壊的操作は行わない。

## Phase 0でスコープ外

North Star §5.6のうち、T-015/T-016では次を実装しない。

- AuthN/AuthZ
- Pre-execution guardrail / Post-execution guardrail
- Dry-run
- Approval
- Rate limit
- Test asset accessのread-only index化
- Performance tool control

T-015/T-016の責務はallowlist、input/output schema validation、Trace Storeへのredacted audit log保存の最小実装に限定する。
