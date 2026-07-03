# Sandbox Runner

T-020のPhase 0最小runner。ADR-0004に従い、process + temporary directory based
sandboxでallowlistされたコマンドを実行し、結果とstate diffをExecutionEvidenceとして
Evidence Storeへ保存する。

このrunnerは安全な隔離境界ではなく、決定性検証のための実行境界である。敵対的コード、
network egress、secret isolation、CPU/memory hard limitはPhase 0スコープ外。

## 構成

- `models.py`: shell-free command、run request、run resultのdataclass
- `runner.py`: sandbox準備、command実行、ExecutionEvidence組み立て、Evidence Store保存
- `state_diff.py`: sandbox root配下の相対path基準deterministic state diff
- `errors.py`: runner固有例外

## 実行フロー

1. `SandboxRunRequest.sandbox_root` が無ければ `create`、あれば `reset` する
2. `seed_path` のfixture seedを投入する
3. seed後の `state_hash` と正規化snapshotを取得する
4. `CommandSpec.argv` をshellなしの引数配列で実行する
5. child processへはsandbox用に構築した最小envだけを渡す(PATHは渡さない)
   - `VERIDIA_FIXED_NOW`
   - `PYTHONIOENCODING=utf-8`
6. 実行後の `state_hash` とsnapshotを取得し、相対path基準のstate diffを作る
7. `IdFactory.new_trace_context()` で `run_id` / `trace_id` を採番する
8. ExecutionEvidence artifactを組み立て、`EvidenceStore.save_execution_evidence()` で保存する

## Python API

```python
import sys
from pathlib import Path

from sandbox_runner import CommandSpec, SandboxRunRequest, SandboxRunner

runner = SandboxRunner()
result = runner.run(
    SandboxRunRequest(
        sandbox_root=Path("/tmp/veridia-sandbox"),
        evidence_root=Path("/tmp/veridia-evidence"),
        seed_path=Path("/tmp/fixture-seed.json"),
        seed_id="fixture-t020-deterministic-v1",
        fixed_now="2026-07-03T12:34:56.789012Z",
        test_asset_id="TEST-T020-DETERMINISTIC-SAMPLE",
        command=CommandSpec(
            argv=(sys.executable, "workspace/sample_test.py"),
            allowed_executables=(sys.executable,),
        ),
    )
)

assert result.verdict == "pass"
assert result.stored_evidence.metadata.trace_id == result.artifact["trace_id"]
```

`argv[0]` は絶対pathで、かつ `allowed_executables` に完全一致する必要がある。envは
secret非継承と決定性のためPATH無しの最小構成なので、裸のcommand名は早期に拒否する。
shell展開、glob、環境変数展開には依存しない。

## 決定性の担保

- sandboxは各runで `create` または `reset` してからseedする
- state diffはsandbox rootからの相対path、entry type、file SHA-256、symlink targetだけを見る
- state hashは `sandbox-state-hash-v2`。長さprefix付きframingでentry境界を明示し、file contentは
  1MB chunkでstreaming SHA-256化してからhashへ入れる
- absolute path、mtime、inode、owner、permissionはdiff対象に含めない
- sample testはsynthetic fixtureだけを読み、`VERIDIA_FIXED_NOW` を使って固定時刻を扱う
- test result / state diffの比較では、runごとに変わる `run_id` / `trace_id` / `artifact_id` を含めない

## Phase 0スコープ

実装するもの:

- sandbox rootの準備(create/reset)とfixture seed投入
- allowlistされた単一commandのsubprocess実行
- fixed clock envの注入
- 実行前後のstate hashとdeterministic state diff
- ExecutionEvidence保存とEvidence Storeからの読み出し

実装しないもの:

- 任意repo/test suiteの汎用実行
- network egress control
- secret isolationの強制
- tenant isolation
- CPU/memory hard resource limit
- container runtime adapter
