"""Minimal Phase 0 sandbox runner implementation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from evidence_store import EvidenceStore
from sandbox_env import apply_seed, create, reset, state_hash
from sandbox_env.clock import FIXED_NOW_ENV_VAR
from sandbox_env.hashing import HASH_VERSION as SANDBOX_STATE_HASH_VERSION
from trace_ids import IdFactory

from sandbox_runner.errors import SandboxRunnerError
from sandbox_runner.models import CommandSpec, SandboxRunRequest, SandboxRunResult
from sandbox_runner.state_diff import diff, snapshot

ARTIFACT_VERSION = "0.1.0"
ARTIFACT_TYPE = "execution_evidence"
CREATED_BY = {
    "agent": "sandbox-runner",
    "skill": "execution-evidence-capture",
    "model": "phase-0-local-runner",
}


class SandboxRunner:
    """Prepare a deterministic sandbox, run an allowlisted command, and save evidence."""

    def __init__(self, *, id_factory: IdFactory | None = None) -> None:
        self._id_factory = id_factory or IdFactory()

    def run(self, request: SandboxRunRequest) -> SandboxRunResult:
        """Execute one sandbox test run and persist ExecutionEvidence."""

        _validate_command(request.command)
        sandbox_root = _prepare_sandbox(request)
        before_hash = state_hash(sandbox_root)
        before_snapshot = snapshot(sandbox_root)

        completed = _run_command(request.command, sandbox_root, request.fixed_now)

        after_hash = state_hash(sandbox_root)
        state_diff = diff(before_snapshot, snapshot(sandbox_root))
        test_result = _test_result(request.command, completed)
        trace_context = self._id_factory.new_trace_context()
        artifact = _execution_evidence_artifact(
            request,
            run_id=trace_context.run_id,
            trace_id=trace_context.trace_id,
            before_hash=before_hash,
            after_hash=after_hash,
            state_diff=state_diff,
            test_result=test_result,
        )
        stored = EvidenceStore.open(request.evidence_root).save_execution_evidence(
            artifact,
            test_result=test_result,
            state_diff=state_diff,
            reproduction_bundle=_reproduction_bundle(
                request,
                before_hash=before_hash,
                before_snapshot=before_snapshot,
            ),
            logs={
                "stdout.log": test_result["stdout"].encode("utf-8"),
                "stderr.log": test_result["stderr"].encode("utf-8"),
            },
        )
        return SandboxRunResult(
            artifact=artifact,
            test_result=test_result,
            state_diff=state_diff,
            stored_evidence=stored,
            verdict=test_result["verdict"],
        )


def _prepare_sandbox(request: SandboxRunRequest) -> Path:
    sandbox_root = Path(request.sandbox_root)
    try:
        if sandbox_root.exists():
            reset(sandbox_root)
        else:
            create(sandbox_root)
        apply_seed(sandbox_root, request.seed_path)
    except Exception as exc:
        raise SandboxRunnerError(f"failed to prepare sandbox {sandbox_root}: {exc}") from exc
    return sandbox_root


def _validate_command(command: CommandSpec) -> None:
    if not command.argv:
        raise SandboxRunnerError("command argv must not be empty")
    executable = command.argv[0]
    if not Path(executable).is_absolute():
        raise SandboxRunnerError(f"command executable must be an absolute path: {executable}")
    if executable not in command.allowed_executables:
        raise SandboxRunnerError(f"command executable is not allowlisted: {executable}")


def _run_command(
    command: CommandSpec,
    sandbox_root: Path,
    fixed_now: str,
) -> subprocess.CompletedProcess[str]:
    env = {
        FIXED_NOW_ENV_VAR: fixed_now,
        "PYTHONIOENCODING": "utf-8",
    }
    try:
        return subprocess.run(
            list(command.argv),
            cwd=sandbox_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=command.timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            args=list(command.argv),
            returncode=124,
            stdout=_timeout_text(exc.stdout),
            stderr=_timeout_text(exc.stderr) + f"\ntimeout after {command.timeout_seconds}s\n",
        )
    except OSError as exc:
        raise SandboxRunnerError(
            f"failed to execute sandbox command {command.argv!r}: {exc}"
        ) from exc


def _test_result(
    command: CommandSpec,
    completed: subprocess.CompletedProcess[str],
) -> dict[str, Any]:
    verdict = "pass" if completed.returncode == 0 else "fail"
    return {
        "version": "sandbox-test-result.v1",
        "argv": list(command.argv),
        "exit_code": completed.returncode,
        "verdict": verdict,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _tool_call_status(test_result: dict[str, Any]) -> str:
    if test_result["exit_code"] == 124:
        return "timeout"
    if test_result["verdict"] == "pass":
        return "success"
    return "failure"


def _reproduction_bundle(
    request: SandboxRunRequest,
    *,
    before_hash: str,
    before_snapshot: dict[str, Any],
) -> dict[str, Any]:
    return {
        "version": "sandbox-reproduction-bundle.v1",
        "seed": {
            "id": request.seed_id,
            "path": str(request.seed_path),
        },
        "fixed_now": request.fixed_now,
        "command": {
            "argv": list(request.command.argv),
            "allowed_executables": list(request.command.allowed_executables),
            "timeout_seconds": request.command.timeout_seconds,
        },
        "state_before": {
            "hash": before_hash,
            "hash_version": SANDBOX_STATE_HASH_VERSION,
            "entries": [entry.to_json() for entry in before_snapshot.values()],
        },
    }


def _execution_evidence_artifact(
    request: SandboxRunRequest,
    *,
    run_id: str,
    trace_id: str,
    before_hash: str,
    after_hash: str,
    state_diff: dict[str, Any],
    test_result: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = f"ART-EVIDENCE-{run_id}"
    return {
        "artifact_id": artifact_id,
        "artifact_type": ARTIFACT_TYPE,
        "version": ARTIFACT_VERSION,
        "source_refs": [f"internal://test-assets/{request.test_asset_id}"],
        "created_by": CREATED_BY,
        "confidence": 1.0 if test_result["verdict"] == "pass" else 0.0,
        "status": "draft",
        "requires_human_review": True,
        "trace_id": trace_id,
        "created_at": request.fixed_now,
        "run_id": run_id,
        "test_asset_id": request.test_asset_id,
        "environment": {
            "env_id": "phase-0-process-sandbox",
            "seed": request.seed_id,
            "clock": request.fixed_now,
        },
        "inputs": {
            "seed": request.seed_id,
            "command": list(request.command.argv),
            "allowlisted_executable": request.command.argv[0],
        },
        "outputs": {
            "verdict": test_result["verdict"],
            "exit_code": test_result["exit_code"],
        },
        "state_before": {"hash": before_hash, "hash_version": SANDBOX_STATE_HASH_VERSION},
        "state_after": {"hash": after_hash, "hash_version": SANDBOX_STATE_HASH_VERSION},
        "state_diff": {
            "summary": state_diff["summary"],
        },
        "tool_calls": [
            {
                "name": "sandbox_runner.command",
                "status": _tool_call_status(test_result),
                "argv": list(request.command.argv),
            }
        ],
        "logs": [],
        "screenshots": [],
        "grader_results": [{"verdict": test_result["verdict"], "score": 1.0}],
        "verdict": test_result["verdict"],
        "reproduction_bundle": f"object-storage://evidence/{run_id}/reproduction-bundle.json",
    }


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
