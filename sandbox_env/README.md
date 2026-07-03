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

`state_hash` はsandbox root配下を相対path順に走査し、相対path、file type、file contentから
SHA-256を計算する。absolute path、mtime、inode、owner、permissionはhashへ含めない。

default rootは `.veridia/sandbox/runs/` 配下だが、pytestや動作確認では必ず `tmp_path` や
`/tmp` 配下の明示rootを渡す。repo直下に `.veridia` を作らない。

## Python API

```python
from sandbox_env import create, destroy, reset, state_hash

env = create(tmp_path / "sandbox")
initial = state_hash(env.root)
reset(env.root)
assert state_hash(env.root) == initial
destroy(env.root)
```

`reset` はsnapshotやoverlay filesystemではなく、削除後に同じmanifestから再作成する。
T-019のfixture seedはこの初期状態の上に投入する別層であり、T-018の初期状態hashとは分けて扱う。

## CLI

```bash
SANDBOX_ROOT="$(mktemp -d)/sandbox"

uv run python -m sandbox_env create "$SANDBOX_ROOT"
uv run python -m sandbox_env state-hash "$SANDBOX_ROOT"
uv run python -m sandbox_env reset "$SANDBOX_ROOT"
uv run python -m sandbox_env destroy "$SANDBOX_ROOT"
```

`create` は既存rootを上書きしない。初期化済みrootを作り直す場合は `reset` を使う。

## Phase 0スコープ

ADR-0004の§5.7範囲表に合わせ、T-018では次だけを扱う。

- 実装: ephemeral envの `create` / `destroy` / `reset`
- 実装: resetをsnapshot/rollbackの最小代替として扱う
- 実装: 初期状態の `state_hash`
- 最小担保: synthetic fixtureと明示rootだけを対象にし、本番write先を渡さない

次はPhase 0のT-018では実装しない。

- deterministic clock: T-019/T-020で `VERIDIA_FIXED_NOW` とclock helperとして扱う
- seeded fixtures: T-019でreset後に再投入できる別層として扱う
- mock external services
- network egress control
- secrets isolationの強制
- tenant isolation
- CPU/memory hard resource limit
- performance sandbox

このruntimeは敵対的コードを閉じ込める安全境界ではない。任意外部通信、secret流出、resource abuse、
tenant越境を機械的に防ぐものではなく、Phase 0の決定性検証に限定して使う。
