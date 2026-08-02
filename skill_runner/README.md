# skill_runner/ — sqk-core skillの実行境界

sqk-coreのskillを隔離環境で1回実行し、出力を契約検証してから `RunRecord` として保存する。

- 実行方式: [ADR-0005](../docs/decisions/adr-0005-llm-skill-execution.md)
- 契約の正本: [ADR-0007](../docs/decisions/adr-0007-sqk-core-contract-consumption.md)(sqk-core)
- タスク: [T-027](../docs/tasks/phase-1/T-027-skill-runner-minimal.md)

## 使い方

```python
from run_store import RunStore
from skill_runner import ClaudeCliLLMClient, SkillRunner
from trace_store import TraceStore

runner = SkillRunner(
    llm_client=ClaudeCliLLMClient(),          # backendは常にDIで注入する
    run_store=RunStore.open(".veridia/store/runs"),
    trace_store=TraceStore.open(".veridia/store/trace"),
)

result = runner.run(
    "test-architecture-design",               # sqk-coreのskill名
    input_text=feature_description,           # 信頼できない入力(データ部)
    source_refs=["internal://github/org/repo/pull/123"],
    agent="veridia-skill-runner",
)
print(result.run_id, result.record["envelope"]["gate_status"])
```

`run_id` / `trace_id` は呼び出し側から渡さない。`trace_ids` の契約(T-012)に従った形式でなければ
Trace Store と突き合わせられないため、runnerが `IdFactory` で採番する。

## 実行の流れ

```text
skill読み込み(固定SHA)→ prompt生成 → LLM呼び出し → envelope検証(sqk-core契約)
  → RunRecordへwrap → 保存 → run_metricsをTrace Storeへ
```

各段が通らなければ次へ進まない。**宣言した `schema_ref` を満たさない出力は保存されない。**
metricsは保存の後に書くので、保存済みのrunには必ずtraceがある。

## 境界

| 境界 | 責務 |
|---|---|
| `LLMClient`(Protocol) | モデル推論のみ。artifactの意味を知らない。Tool Gatewayとは**並列**であり、その上には載せない([ADR-0005](../docs/decisions/adr-0005-llm-skill-execution.md) Decision 3) |
| `SqkSkillSource` | 固定SHAのsubmoduleから `SKILL.md` を読む |
| `SkillRunner` | prompt組み立て・検証・保存・metricsの統合 |

### backendは環境変数から選べない

`FakeLLMClient` はテストからのDIでのみ使う。環境変数で `fake` を選べるようにすると、設定漏れの
まま本番runが走り、**偽のartifactが `status: draft` で保存される**。検出が難しく害が大きい。

## skillの読み込み元

`vendor/sqk-core/skills/<name>/SKILL.md` を**veridiaが明示的に読む**。Claude Codeのskill発見機構
(`.claude/skills`)には依存しない。ADR-0005 Decision 5.1 / 5.2 がcwdをリポジトリ外に置き、skill
読み込みを抑止するため、発見機構は原理的に届かない([ADR-0005 末尾の追記](../docs/decisions/adr-0005-llm-skill-execution.md))。

明示的に読む利点として、**どのSKILL.md本文を渡したかがpromptとして残り**、固定SHAと結び付く
(`RunRecord.sqk_core.commit`)。

## 出力schemaの二段構え

CLIには **portable profile**(`type` / `properties` / `required` / `enum` / `items` /
`additionalProperties`)の範囲のschemaだけを渡す(ADR-0005 Decision 6.1)。`pattern` や `oneOf` は
CLI側で拘束せず、`artifact_validator` が sqk-core の実契約で強制する。

profile外の制約は **`contract_note` がschemaから導出してprompt(指示部)へ載せる。**
これが無いと、モデルは検証される制約を知らないまま出力し、呼び出しコストだけ払って破棄される。

> 実測(2026-08-02): contract note が無い状態で `test-architecture-design` を cold start
> 実行したところ、`DTC-A01` / `DTC-B02` 形式のグループIDを合成し `^DTC-[0-9]+$` に弾かれた。

## 隔離

`ClaudeCliLLMClient` は毎回、リポジトリ外の一時ディレクトリをcwdにし、**祖先に
`CLAUDE.md` / `AGENTS.md` / VCSルートが無いことを実行前に検証する**(`IsolationError`)。
`CLAUDE.md` / `AGENTS.md` は祖先方向へ探索されるため「空ディレクトリ」は隔離条件にならない。

CLIへは隔離フラグを毎回明示する(`--safe-mode` / `--setting-sources ""` /
`--disable-slash-commands` / `--strict-mcp-config` / `--tools ""` / `--no-session-persistence`)。
`--bare` は使わない(サブスクリプション認証と両立しないため。Decision 4)。

**効果の実測(2026-08-02):** 隔離なしの計測(ADR-0005)では cache_creation 35,447 tokens
だったのに対し、隔離フラグ適用後は 2,361 tokens。約1/15。

## 認証

**veridiaは資格情報に一切触れない。** API keyを読まず、要求せず、未設定を異常として扱わない。
認証はCLI自身の資格情報ストアに委ねる。`verify_available()` が実行前に次を確認する。

1. CLIが起動できる
2. バージョンがallowlistに含まれる(現在: `claude` 2.1.207 のみ)
3. capability probe(認証済みかつ `--json-schema` が効く)

allowlistの追加は**実測検証とセット**で行う。CLIはAPIのようなバージョン契約を持たない。

## 実LLMスモーク(CIには含めない)

```bash
uv run python -c "
from pathlib import Path
from run_store import RunStore
from skill_runner import ClaudeCliLLMClient, SkillRunner
from trace_store import TraceStore
root = Path('.veridia/smoke')
r = SkillRunner(llm_client=ClaudeCliLLMClient(),
                run_store=RunStore.open(root/'runs'), trace_store=TraceStore.open(root/'trace'))
res = r.run('test-architecture-design', input_text='対象機能の説明を1〜3文で',
            source_refs=['internal://example/pr/1'], agent='smoke')
print(res.run_id, res.record['envelope']['gate_status'])
"
```

`uv run pytest` は実LLMを呼ばない(`FakeLLMClient` をDIで注入する)。
