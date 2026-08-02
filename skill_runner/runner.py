"""Run one sqk-core skill and persist the result as an auditable RunRecord.

The sequence is fixed and every step must pass before the next runs:

    load skill (pinned SHA) → render prompt → LLM → validate envelope against the
    sqk-core contract → wrap as RunRecord → save → record run metrics

An output that does not satisfy the contract it declares never becomes a stored
record. Metrics are written after the save so a stored run always has a trace.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from artifact_validator import declares_sqk_core_contract, validate_handoff_envelope
from run_store import RunStore, build_run_record
from trace_ids import IdFactory, TraceContext
from trace_store import RUN_METRICS_EVENT, TraceStore

from skill_runner.contract_note import contract_note
from skill_runner.envelope_schema import portable_envelope_schema
from skill_runner.errors import SkillRunnerError
from skill_runner.llm_client import LLMClient, Prompt
from skill_runner.skill_source import SkillSource, SqkSkillSource

SQK_ROOT = Path(__file__).resolve().parent.parent / "vendor" / "sqk-core"
ARTIFACTS_FIELD = "artifacts"
CONTENT_FIELD = "content"
ITEMS_FIELD = "items"
SUCCESS_STATUS = "success"
GIT_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class SkillRunResult:
    """What one skill run produced, for callers that want more than the stored record."""

    run_id: str
    trace_id: str
    record: dict[str, Any]
    record_path: Path


@dataclass(frozen=True)
class SkillRunner:
    """Execute a sqk-core skill through an injected LLM backend."""

    llm_client: LLMClient
    run_store: RunStore
    trace_store: TraceStore
    skill_source: SkillSource = SqkSkillSource()
    id_factory: IdFactory = IdFactory()

    def run(
        self,
        skill_name: str,
        *,
        input_text: str,
        source_refs: Sequence[str],
        agent: str,
        data_refs: Sequence[str] = (),
        authoritative_fields: Mapping[str, Any] | None = None,
    ) -> SkillRunResult:
        """Run one skill end to end and return the stored record.

        `authoritative_fields` are values whose authority is **not** the model: they are
        written over every produced artifact before validation, whatever the model said
        (ADR-0009 Decision 2 / ADR-0010). `trust_level` is the first of them — a trust
        label the labelled party writes about itself is a gate it can walk around.

        Raises:
            SkillNotFoundError / SkillSourceError: the skill could not be loaded.
            BackendUnavailableError: the backend is unusable (checked before spending).
            LLMInvocationError: the backend returned nothing usable.
            ArtifactValidationError: the envelope or the record breaks its contract.
        """
        if not source_refs:
            raise SkillRunnerError(
                "source_refs must not be empty: an artifact without a source cannot pass "
                "the source grounding gate (§6.1)"
            )

        skill = self.skill_source.load(skill_name)
        self.llm_client.verify_available()
        # IDs are minted here, not accepted from callers: they must match the trace_ids
        # contract (T-012) or the record cannot be correlated with the Trace Store
        context = self.id_factory.new_trace_context()

        prompt = Prompt(
            instructions=_instructions(skill),
            data=input_text,
            data_refs=tuple(data_refs) or tuple(source_refs),
        )
        response = self.llm_client.complete(
            prompt,
            output_schema=portable_envelope_schema(skill.output_schema_refs),
        )

        envelope = _with_authoritative_fields(response.output, authoritative_fields)
        validate_handoff_envelope(envelope)

        record = build_run_record(
            envelope,
            run_id=context.run_id,
            trace_id=context.trace_id,
            agent=agent,
            model=response.model,
            source_refs=list(source_refs),
            created_at=datetime.now(UTC),
            # Only a run that actually used a sqk-core contract pins its SHA (ADR-0010)
            sqk_core_commit=(
                _pinned_sqk_core_commit()
                if declares_sqk_core_contract(envelope.get(ARTIFACTS_FIELD))
                else None
            ),
        )
        record_path = self.run_store.save(record)
        self._record_run_metrics(skill_name, context, response)
        return SkillRunResult(
            run_id=context.run_id,
            trace_id=context.trace_id,
            record=record,
            record_path=record_path,
        )

    def _record_run_metrics(
        self,
        skill_name: str,
        context: TraceContext,
        response: Any,
    ) -> None:
        """Save token / cost metrics to the Trace Store (ADR-0005 Decision C1 / §15.2).

        Metrics only: no prompt text reaches the Trace Store from here.
        """
        now = _format_utc(datetime.now(UTC))
        self.trace_store.save_record(
            context,
            sequence=1,
            event_type=RUN_METRICS_EVENT,
            name=f"skill:{skill_name}",
            status=SUCCESS_STATUS,
            started_at=now,
            ended_at=now,
            redacted_args=_metrics(response),
        )


def _with_authoritative_fields(
    envelope: Mapping[str, Any],
    fields: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return a copy of the envelope with non-model-owned fields written over.

    Overwriting is unconditional: checking "did the model already set it?" would let a
    model keep its own value by supplying one, which is exactly the bypass this closes.
    The envelope is not mutated — the caller's object stays as the model returned it.
    """
    copied = dict(envelope)
    if not fields:
        return copied
    artifacts = copied.get(ARTIFACTS_FIELD)
    if not isinstance(artifacts, list):
        return copied
    copied[ARTIFACTS_FIELD] = [_artifact_with_fields(artifact, fields) for artifact in artifacts]
    return copied


def _artifact_with_fields(artifact: Any, fields: Mapping[str, Any]) -> Any:
    if not isinstance(artifact, Mapping):
        return artifact
    updated = dict(artifact)
    content = updated.get(CONTENT_FIELD)
    if isinstance(content, Mapping):
        updated[CONTENT_FIELD] = {**content, **fields}
    items = updated.get(ITEMS_FIELD)
    if isinstance(items, list):
        updated[ITEMS_FIELD] = [
            {**item, **fields} if isinstance(item, Mapping) else item for item in items
        ]
    return updated


def _instructions(skill: Any) -> str:
    """Skill body plus the constraints the validator enforces but the CLI cannot."""
    note = contract_note(skill.output_schema_refs)
    return f"{skill.instruction_text}\n\n{note}" if note else skill.instruction_text


def _metrics(response: Any) -> dict[str, Any]:
    return {
        "backend": response.backend,
        "model": response.model,
        "usage": dict(response.usage),
        "reference_cost_usd": response.reference_cost_usd,
    }


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _pinned_sqk_core_commit() -> str:
    """Resolve the sqk-core commit actually checked out, not a value copied from docs."""
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", "-C", str(SQK_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SkillRunnerError(f"failed to resolve the sqk-core commit: {exc}") from exc
    if completed.returncode != 0:
        raise SkillRunnerError(
            f"failed to resolve the sqk-core commit under {SQK_ROOT}: "
            f"{completed.stderr.strip()} (is the submodule checked out?)"
        )
    return completed.stdout.strip()


def default_prompt_data(mapping: Mapping[str, Any]) -> str:
    """Render a mapping as the untrusted data half of a prompt."""
    return json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True)
