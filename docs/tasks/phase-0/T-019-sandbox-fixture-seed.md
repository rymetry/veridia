---
task_id: T-019
epic: sandbox
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-018]
---

# T-019: fixture seed機構とdeterministic clock

## 目的

sandbox内の初期データを明示的にseedし、時刻依存を固定する。同一test再実行の決定性(T-020)の前提。

## 参照

- 計画: §3 WS-D
- North Star: §5.7(Seeded fixtures / Deterministic clock)

## DoD

- [x] seed定義(ファイル形式)からfixtureをsandboxへ投入できる(実行ログで確認)
- [x] reset → 再seedで同一状態になることがテストで実証されている(状態のhash比較等)
- [x] sandbox内で現在時刻が固定され、2回の実行で同一時刻を返すことがテストで確認されている

## 検証方法・根拠

- seed定義形式:
  - JSON object。`version: "sandbox-fixture-seed.v1"`、`directories: string[]`、`files: [{"path": string, "content": string}]`。
  - `path` はsandbox rootからの相対pathのみ。absolute path / `..` を含むpathは拒否する。
  - `content` はUTF-8 textとして書き込む。binary fixtureや外部service mockはT-019スコープ外。
- seed投入の実行ログ:

  ```text
  created: /var/folders/jw/ht4htjb52_xc5kd9x5krxtlc0000gq/T/tmp.743ZhRiBtS/sandbox
  seeded: /var/folders/jw/ht4htjb52_xc5kd9x5krxtlc0000gq/T/tmp.743ZhRiBtS/sandbox
  seed: /var/folders/jw/ht4htjb52_xc5kd9x5krxtlc0000gq/T/tmp.743ZhRiBtS/seed.json
  directories: 1
  files: 2
  7fa2b5f528ad98cbe3fc171899dc88a37093d0bf30dbbba023bd6be612f66cfb
  ```

- seed投入:
  - 検証方法: `tests/test_sandbox_env_seed_clock.py::test_seed_manifest_materializes_declared_fixture_files`
  - 結果: seed manifestから `workspace/data/orders.json` と `workspace/config.json` が作成され、CLIはroot / seed path / directory数 / file数を出力する。
- reset → 再seed同一性:
  - 検証方法: `tests/test_sandbox_env_seed_clock.py::test_reset_then_reseed_produces_the_same_seeded_state_hash`
  - 結果: seed前初期hashとseed後hashが異なり、`reset` 後に同じseedを再投入したseed後hashが一致する。
- deterministic clock:
  - 検証方法: `tests/test_sandbox_env_seed_clock.py::test_fixed_clock_returns_same_utc_time_in_repeated_sandbox_subprocesses`
  - 結果: sandbox rootを `cwd` にした子プロセスへ `VERIDIA_FIXED_NOW=2026-07-03T12:34:56.789012Z` を渡し、`sandbox_env.clock.now()` が2回とも `2026-07-03T12:34:56.789012+00:00` を返す。
  - 不正値: `tests/test_sandbox_env_seed_clock.py::test_clock_rejects_invalid_fixed_now_with_context` でtimezone無しの `VERIDIA_FIXED_NOW` を `SandboxEnvError` として拒否する。
- 実行結果:
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest tests/test_sandbox_env_seed_clock.py -q` → `5 passed`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run pytest` → `456 passed`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff check .` → `All checks passed!`
  - `UV_CACHE_DIR=${TMPDIR:-/tmp}/uv-cache uv run ruff format --check .` → `73 files already formatted`

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし
