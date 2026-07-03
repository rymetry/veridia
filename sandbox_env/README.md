# Sandbox Env

T-018のPhase 0最小sandbox environment。ADR-0004に従い、containerではなく
process + temporary directory based ephemeral envを実装する。目的は安全な隔離ではなく、
同じ初期状態からsandboxを作り直せることを検証するための実行境界である。

## 構成

`create` はsandbox rootを作成し、コード上のdeterministic manifestから初期状態を配置する。

```text
<sandbox-root>/
  artifacts/
  manifest.json
  tmp/
  workspace/
    README.md
```

`state_hash` はsandbox root配下を相対path順に走査し、相対path、file type、file SHA-256、
symlink targetから `sandbox-state-hash-v2` のSHA-256を計算する。entryは長さprefix付きで
framingし、file contentは1MB chunkでstreaming hashする。absolute path、mtime、inode、owner、
permissionはhashへ含めない。

default rootは `.veridia/sandbox/runs/` 配下だが、pytestや動作確認では必ず `tmp_path` や
`/tmp` 配下の明示rootを渡す。repo直下に `.veridia` を作らない。

## Python API

```python
from sandbox_env import apply_seed, create, destroy, reset, state_hash
from sandbox_env.clock import now

env = create(tmp_path / "sandbox")
initial = state_hash(env.root)
reset(env.root)
assert state_hash(env.root) == initial

apply_seed(env.root, tmp_path / "seed.json")
seeded = state_hash(env.root)
reset(env.root)
apply_seed(env.root, tmp_path / "seed.json")
assert state_hash(env.root) == seeded

current_time = now()
destroy(env.root)
```

`reset` はsnapshotやoverlay filesystemではなく、削除後に同じmanifestから再作成する。Phase 0は
同一sandbox rootに対する単一writer前提で、destroy→create間をlockする並行writer対策は実装しない。
T-019のfixture seedはこの初期状態の上に投入する別層であり、T-018の初期状態hashとは分けて扱う。

## Fixture Seed

fixture seedは、作成済みsandbox rootへ投入する別層である。seed前に `create` または `reset` で
初期状態を作り、同じseed定義を再投入すると同じseed後状態hashになる。

seed定義はJSONで、相対pathとUTF-8 text contentだけを宣言する。absolute pathや `..` を含むpathは
拒否する。

```json
{
  "version": "sandbox-fixture-seed.v1",
  "directories": ["workspace/data"],
  "files": [
    {
      "path": "workspace/data/orders.json",
      "content": "[{\"id\":\"order-fixture-001\",\"status\":\"paid\"}]\n"
    },
    {
      "path": "workspace/config.json",
      "content": "{\"feature_flags\":{\"checkout_v2\":true}}\n"
    }
  ]
}
```

Python API:

```python
from sandbox_env import apply_seed

result = apply_seed("/tmp/veridia-sandbox", "/tmp/fixture-seed.json")
assert result.file_count == 2
```

## CLI

```bash
SANDBOX_ROOT="$(mktemp -d)/sandbox"

uv run python -m sandbox_env create "$SANDBOX_ROOT"
uv run python -m sandbox_env seed "$SANDBOX_ROOT" /tmp/fixture-seed.json
uv run python -m sandbox_env state-hash "$SANDBOX_ROOT"
uv run python -m sandbox_env reset "$SANDBOX_ROOT"
uv run python -m sandbox_env destroy "$SANDBOX_ROOT"
```

`create` は既存rootを上書きしない。初期化済みrootを作り直す場合は `reset` を使う。
`seed` は実行ログとしてsandbox root、seed定義path、作成対象のdirectory数、file数を出力する。

## Deterministic Clock

Phase 0の時刻固定は、ADR-0004どおり `VERIDIA_FIXED_NOW` とclock helperで行う。
`sandbox_env.clock.now()` は `VERIDIA_FIXED_NOW` がある場合だけその値をUTCの
timezone-aware `datetime` として返し、ない場合は実時刻のUTC `datetime` を返す。

```bash
VERIDIA_FIXED_NOW=2026-07-03T12:34:56.789012Z \
  uv run python -c 'from sandbox_env.clock import now; print(now().isoformat())'
```

不正な値、timezone無しの値、UTC以外のoffsetは `SandboxEnvError` として拒否する。Phase 0方式は
OS clockを偽装しないため、sandbox内で実行するveridia側コードとsample testは直接
`datetime.now()` を呼ばず、このhelperまたは注入されたclock abstractionを使う。

## Phase 0スコープ

ADR-0004の§5.7範囲表に合わせ、T-018/T-019では次だけを扱う。

- 実装: ephemeral envの `create` / `destroy` / `reset`
- 実装: resetをsnapshot/rollbackの最小代替として扱う
- 実装: 初期状態の `state_hash`
- 実装: reset後に再投入できるfixture seed層
- 実装: `VERIDIA_FIXED_NOW` によるdeterministic clock helper
- 最小担保: synthetic fixtureと明示rootだけを対象にし、本番write先を渡さない

次はPhase 0のT-018/T-019では実装しない。

- mock external services
- network egress control
- secrets isolationの強制
- tenant isolation
- CPU/memory hard resource limit
- performance sandbox

このruntimeは敵対的コードを閉じ込める安全境界ではない。任意外部通信、secret流出、resource abuse、
tenant越境を機械的に防ぐものではなく、Phase 0の決定性検証に限定して使う。
