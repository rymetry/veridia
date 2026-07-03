---
task_id: T-018
epic: sandbox
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: done
owner:
blocked_by: [T-002, T-017]
---

# T-018: sandbox ephemeral env(作成・破棄・reset)

## 目的

trialごとに使い捨てられる隔離実行環境の最小版を実装する。fixture(T-019)とrunner(T-020)の土台。

## 参照

- 計画: §3 WS-D、§6(最小実装に留める)
- North Star: §5.7(Ephemeral env / Snapshot・rollback)

## DoD

- [x] コマンド1発でsandbox環境の新規作成・破棄・resetができる(実行ログで確認)
- [x] 2回連続で作成(またはreset)した環境が同一の初期状態であることがテストで実証されている(状態のhash比較等)
- [x] §5.7の要件のうちPhase 0で実装しない項目(network egress control / tenant isolation等)がREADMEにスコープ外として明記されている

## 検証方法・根拠

- コマンド1発でsandbox環境の新規作成・破棄・resetができる:
  - 検証方法: repo外の一時ディレクトリ配下をrootにして `python -m sandbox_env create|state-hash|reset|destroy` を実行。
  - 結果: 次のログで、create、mutation後reset、hash一致、destroy後削除を確認。

```text
created: /var/folders/jw/ht4htjb52_xc5kd9x5krxtlc0000gq/T/tmp.diSIPVfHtm/sandbox
first-hash: 424d816f59371e500ae4d6997db32c25adad443523687119b07231e23fcc59db
reset: /var/folders/jw/ht4htjb52_xc5kd9x5krxtlc0000gq/T/tmp.diSIPVfHtm/sandbox
second-hash: 424d816f59371e500ae4d6997db32c25adad443523687119b07231e23fcc59db
destroyed: /var/folders/jw/ht4htjb52_xc5kd9x5krxtlc0000gq/T/tmp.diSIPVfHtm/sandbox
destroy-check: removed
```

- 2回連続で作成(またはreset)した環境が同一の初期状態である:
  - 検証方法: `tests/test_sandbox_env.py::test_two_consecutive_creates_have_same_initial_state_hash`
  - 結果: `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run pytest tests/test_sandbox_env.py -q` でpass。`create -> state_hash -> destroy -> create -> state_hash` のhash一致を確認。
- reset後の環境が初期状態に戻る:
  - 検証方法: `tests/test_sandbox_env.py::test_reset_recreates_initial_state_after_mutation`
  - 結果: 同上のpytestでpass。`workspace/scratch.txt` を追加した後、`reset` で消え、初期hashに戻ることを確認。
- §5.7のうちPhase 0で実装しない項目のREADME記載:
  - 検証方法: `sandbox_env/README.md` を確認。
  - 結果: mock external services / network egress control / secrets isolationの強制 / tenant isolation / CPU・memory hard resource limit / performance sandbox等をT-018スコープ外として記載。ADR-0004準拠で安全境界ではないことも明記。
- 全体検証:
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run pytest`: 451 passed
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run ruff check .`: All checks passed
  - `UV_CACHE_DIR="$TMPDIR/uv-cache" uv run ruff format --check .`: 70 files already formatted

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: なし(ADR-0004の範囲内で実装。新規設計判断なし)
