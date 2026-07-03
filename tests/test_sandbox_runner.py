"""T-020 sandbox runner integration tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sandbox_runner import (
    CommandSpec,
    SandboxRunner,
    SandboxRunRequest,
)

FIXED_NOW = "2026-07-03T12:34:56.789012Z"
TEST_ASSET_ID = "TEST-T020-DETERMINISTIC-SAMPLE"


def write_seed_manifest(path: Path) -> Path:
    script = """\
from __future__ import annotations

import json
import os
from pathlib import Path

orders = json.loads(Path("workspace/data/orders.json").read_text(encoding="utf-8"))
result = {
    "fixed_now": os.environ["VERIDIA_FIXED_NOW"],
    "order_count": len(orders),
    "paid_order_ids": [order["id"] for order in orders if order["status"] == "paid"],
}
Path("artifacts/sample-result.json").write_text(
    json.dumps(result, sort_keys=True) + "\\n",
    encoding="utf-8",
)
print(json.dumps({"status": "ok", **result}, sort_keys=True))
"""
    path.write_text(
        json.dumps(
            {
                "version": "sandbox-fixture-seed.v1",
                "directories": ["workspace/data"],
                "files": [
                    {
                        "path": "workspace/data/orders.json",
                        "content": ('[{"id":"order-fixture-001","status":"paid","amount":1200}]\n'),
                    },
                    {
                        "path": "workspace/sample_test.py",
                        "content": script,
                    },
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def make_request(tmp_path: Path, sandbox_name: str) -> SandboxRunRequest:
    seed_path = write_seed_manifest(tmp_path / f"{sandbox_name}-seed.json")
    return SandboxRunRequest(
        sandbox_root=tmp_path / sandbox_name,
        evidence_root=tmp_path / "evidence",
        seed_path=seed_path,
        seed_id="fixture-t020-deterministic-v1",
        fixed_now=FIXED_NOW,
        test_asset_id=TEST_ASSET_ID,
        command=CommandSpec(
            argv=(sys.executable, "workspace/sample_test.py"),
            allowed_executables=(sys.executable,),
        ),
    )


def comparable_result(result: dict[str, object]) -> dict[str, object]:
    return {
        "verdict": result["verdict"],
        "exit_code": result["exit_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }


def test_runner_executes_sample_test_and_saves_execution_evidence(tmp_path: Path) -> None:
    runner = SandboxRunner()
    request = make_request(tmp_path, "sandbox")

    result = runner.run(request)

    assert result.verdict == "pass"
    assert result.state_diff["added"] == [
        {
            "path": "artifacts/sample-result.json",
            "sha256": result.state_diff["added"][0]["sha256"],
            "type": "file",
        }
    ]
    stored = result.stored_evidence
    assert stored.metadata.artifact_id == result.artifact["artifact_id"]
    assert stored.metadata.run_id == result.artifact["run_id"]
    assert stored.metadata.trace_id == result.artifact["trace_id"]
    assert stored.payload["test_asset_id"] == TEST_ASSET_ID
    assert stored.payload["environment"]["clock"] == FIXED_NOW
    assert stored.test_result["verdict"] == "pass"
    assert stored.test_result["stdout"] == (
        '{"fixed_now": "2026-07-03T12:34:56.789012Z", '
        '"order_count": 1, "paid_order_ids": ["order-fixture-001"], "status": "ok"}\n'
    )
    assert stored.state_diff == result.state_diff
    assert stored.logs == {
        "stdout.log": stored.test_result["stdout"].encode(),
        "stderr.log": b"",
    }


def test_same_sample_test_run_twice_has_same_result_and_state_diff(tmp_path: Path) -> None:
    runner = SandboxRunner()

    first = runner.run(make_request(tmp_path, "sandbox-a"))
    second = runner.run(make_request(tmp_path, "sandbox-b"))

    assert comparable_result(first.test_result) == comparable_result(second.test_result)
    assert first.state_diff == second.state_diff


def test_each_run_has_ids_and_can_be_read_from_evidence_store(tmp_path: Path) -> None:
    from evidence_store import EvidenceStore
    from trace_ids import RUN_ID_RE, TRACE_ID_RE

    runner = SandboxRunner()
    first = runner.run(make_request(tmp_path, "sandbox-a"))
    second = runner.run(make_request(tmp_path, "sandbox-b"))
    store = EvidenceStore.open(tmp_path / "evidence")

    assert RUN_ID_RE.fullmatch(first.artifact["run_id"])
    assert TRACE_ID_RE.fullmatch(first.artifact["trace_id"])
    assert first.artifact["run_id"] != second.artifact["run_id"]
    assert first.artifact["trace_id"] != second.artifact["trace_id"]

    by_artifact_id = store.get_by_artifact_id(first.artifact["artifact_id"])
    by_trace_id = store.find_by_trace_id(first.artifact["trace_id"])

    assert by_artifact_id.metadata.run_id == first.artifact["run_id"]
    assert tuple(record.metadata.artifact_id for record in by_trace_id) == (
        first.artifact["artifact_id"],
    )
    assert by_artifact_id.test_result["verdict"] == "pass"
    assert by_artifact_id.state_diff == first.state_diff
