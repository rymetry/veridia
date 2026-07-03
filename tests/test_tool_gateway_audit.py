"""T-016 Tool Gateway audit log integration tests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

FIXED_NOW = datetime(2026, 7, 3, 12, 34, 56, 789012, tzinfo=UTC)
MASK = "<redacted>"


class CountingTokenHex:
    """Deterministic `secrets.token_hex` replacement for audit tests."""

    def __init__(self) -> None:
        self._counter = 0

    def __call__(self, nbytes: int) -> str:
        self._counter += 1
        return f"{self._counter:0{nbytes * 2}x}"[-nbytes * 2 :]


def make_audited_gateway(tmp_path: Path, *, allowlist: frozenset[str]):
    from tool_gateway import AuditedToolGateway, ToolGateway
    from trace_ids import IdFactory
    from trace_store import TraceStore

    factory = IdFactory(clock=lambda: FIXED_NOW, token_hex=CountingTokenHex())
    parent_context = factory.new_trace_context()
    gateway = ToolGateway(registry=make_registry(), allowlist=allowlist)
    trace_store = TraceStore.open(tmp_path / "trace")
    audited_gateway = AuditedToolGateway(
        gateway=gateway,
        trace_store=trace_store,
        parent_context=parent_context,
        id_factory=factory,
        clock=lambda: FIXED_NOW,
    )
    return audited_gateway, trace_store, parent_context


def make_registry():
    from tool_gateway import ToolDefinition, ToolRegistry

    return ToolRegistry.from_definitions(
        (
            ToolDefinition(
                name="fixture.echo",
                input_schema={
                    "type": "object",
                    "required": ["message"],
                    "properties": {
                        "message": {"type": "string"},
                        "api_token": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "required": ["message", "ok"],
                    "properties": {
                        "message": {"type": "string"},
                        "ok": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                handler=_echo_handler,
            ),
        )
    )


def _echo_handler(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"message": str(payload["message"]), "ok": True}


def test_redacts_secret_like_argument_keys_recursively() -> None:
    from tool_gateway import redact_tool_args

    redacted = redact_tool_args(
        {
            "message": "keep",
            "api_token": "DUMMY_API_TOKEN_VALUE",
            "metadata": {
                "password": "DUMMY_PASSWORD_VALUE",
                "safe": "visible",
                "headers": {"Authorization": "Bearer DUMMY_AUTH_VALUE"},
                "items": [{"client_secret": "DUMMY_CLIENT_SECRET_VALUE", "name": "item"}],
            },
        }
    )

    assert redacted == {
        "message": "keep",
        "api_token": MASK,
        "metadata": {
            "password": MASK,
            "safe": "visible",
            "headers": {"Authorization": MASK},
            "items": [{"client_secret": MASK, "name": "item"}],
        },
    }


@pytest.mark.parametrize(
    "key",
    [
        "jwt",
        "cookie",
        "credential",
        "credentials",
        "pwd",
        "passwd",
        "private_key",
        "session",
        "bearer",
        "access_key",
        "refresh_token",
    ],
)
def test_redacts_additional_secret_like_key_names(key: str) -> None:
    from tool_gateway import redact_tool_args

    redacted = redact_tool_args({"metadata": {key: "DUMMY_SECRET_VALUE"}})

    assert redacted == {"metadata": {key: MASK}}


def test_gateway_tool_call_is_saved_with_trace_id_and_redacted_args(tmp_path: Path) -> None:
    audited_gateway, trace_store, parent_context = make_audited_gateway(
        tmp_path,
        allowlist=frozenset({"fixture.echo"}),
    )

    result = audited_gateway.execute(
        "fixture.echo",
        {
            "message": "hello",
            "api_token": "DUMMY_API_TOKEN_VALUE",
            "metadata": {"password": "DUMMY_PASSWORD_VALUE", "safe": "visible"},
        },
    )

    records = trace_store.find_by_trace_id(parent_context.trace_id)
    serialized_args = json.dumps(records[0].redacted_args, sort_keys=True)
    assert result == {"message": "hello", "ok": True}
    assert len(records) == 1
    assert records[0].run_id == parent_context.run_id
    assert records[0].trace_id == parent_context.trace_id
    assert records[0].span_id != parent_context.span_id
    assert records[0].parent_span_id == parent_context.span_id
    assert records[0].sequence == 1
    assert records[0].event_type == "tool_call"
    assert records[0].name == "fixture.echo"
    assert records[0].status == "success"
    assert records[0].latency_ms is not None
    assert records[0].latency_ms >= 0
    assert records[0].redacted_args["api_token"] == MASK
    assert records[0].redacted_args["metadata"]["password"] == MASK
    assert "DUMMY_API_TOKEN_VALUE" not in serialized_args
    assert "DUMMY_PASSWORD_VALUE" not in serialized_args
    assert records[0].result_summary is not None
    assert "message" in records[0].result_summary
    assert records[0].error_summary is None


def test_rejected_tool_call_is_saved_with_error_status(tmp_path: Path) -> None:
    from tool_gateway import ToolNotAllowedError

    audited_gateway, trace_store, parent_context = make_audited_gateway(
        tmp_path,
        allowlist=frozenset(),
    )

    with pytest.raises(ToolNotAllowedError):
        audited_gateway.execute(
            "fixture.echo",
            {"message": "hello", "api_token": "DUMMY_API_TOKEN_VALUE"},
        )

    records = trace_store.find_by_trace_id(parent_context.trace_id)
    serialized_args = json.dumps(records[0].redacted_args, sort_keys=True)
    assert len(records) == 1
    assert records[0].event_type == "tool_call"
    assert records[0].name == "fixture.echo"
    assert records[0].status == "error"
    assert records[0].latency_ms is not None
    assert records[0].redacted_args["api_token"] == MASK
    assert "DUMMY_API_TOKEN_VALUE" not in serialized_args
    assert records[0].result_summary is None
    assert records[0].error_summary is not None
    assert "ToolNotAllowedError" in records[0].error_summary


def test_error_summary_redacts_secret_values_from_exception_message(tmp_path: Path) -> None:
    from tool_gateway import AuditedToolGateway, ToolDefinition, ToolGateway, ToolRegistry
    from trace_ids import IdFactory
    from trace_store import TraceStore

    def fail(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        raise RuntimeError(f"credential leaked: {payload['credential']}")

    factory = IdFactory(clock=lambda: FIXED_NOW, token_hex=CountingTokenHex())
    parent_context = factory.new_trace_context()
    audited_gateway = AuditedToolGateway(
        gateway=ToolGateway(
            registry=ToolRegistry.from_definitions(
                (
                    ToolDefinition(
                        name="fixture.fail",
                        input_schema={
                            "type": "object",
                            "required": ["credential"],
                            "properties": {"credential": {"type": "string"}},
                        },
                        output_schema={"type": "object"},
                        handler=fail,
                    ),
                )
            ),
            allowlist=frozenset({"fixture.fail"}),
        ),
        trace_store=TraceStore.open(tmp_path / "trace"),
        parent_context=parent_context,
        id_factory=factory,
        clock=lambda: FIXED_NOW,
    )

    with pytest.raises(RuntimeError, match="credential leaked"):
        audited_gateway.execute("fixture.fail", {"credential": "DUMMY_CREDENTIAL_VALUE"})

    (record,) = audited_gateway.trace_store.find_by_trace_id(parent_context.trace_id)
    assert "DUMMY_CREDENTIAL_VALUE" not in record.error_summary
    assert "<redacted>" in record.error_summary


def test_multiple_tool_calls_share_run_trace_and_record_child_spans(tmp_path: Path) -> None:
    audited_gateway, trace_store, parent_context = make_audited_gateway(
        tmp_path,
        allowlist=frozenset({"fixture.echo"}),
    )

    audited_gateway.execute("fixture.echo", {"message": "first"})
    audited_gateway.execute("fixture.echo", {"message": "second"})

    records = trace_store.find_by_trace_id(parent_context.trace_id)
    assert tuple(record.sequence for record in records) == (1, 2)
    assert {record.run_id for record in records} == {parent_context.run_id}
    assert {record.trace_id for record in records} == {parent_context.trace_id}
    assert tuple(record.parent_span_id for record in records) == (
        parent_context.span_id,
        parent_context.span_id,
    )
    assert records[0].span_id != records[1].span_id


def test_audit_clock_must_be_timezone_aware(tmp_path: Path) -> None:
    from tool_gateway import AuditedToolGateway

    audited_gateway, _trace_store, _parent_context = make_audited_gateway(
        tmp_path,
        allowlist=frozenset({"fixture.echo"}),
    )
    audited_gateway = AuditedToolGateway(
        gateway=audited_gateway.gateway,
        trace_store=audited_gateway.trace_store,
        parent_context=audited_gateway.parent_context,
        id_factory=audited_gateway.id_factory,
        clock=lambda: datetime(2026, 7, 3, 12, 34, 56),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        audited_gateway.execute("fixture.echo", {"message": "hello"})


def test_error_summary_is_truncated_to_240_characters(tmp_path: Path) -> None:
    from tool_gateway import AuditedToolGateway, ToolDefinition, ToolGateway, ToolRegistry
    from trace_ids import IdFactory
    from trace_store import TraceStore

    def fail(_payload: Mapping[str, Any]) -> Mapping[str, Any]:
        raise RuntimeError("x" * 400)

    factory = IdFactory(clock=lambda: FIXED_NOW, token_hex=CountingTokenHex())
    parent_context = factory.new_trace_context()
    audited_gateway = AuditedToolGateway(
        gateway=ToolGateway(
            registry=ToolRegistry.from_definitions(
                (
                    ToolDefinition(
                        name="fixture.long_error",
                        input_schema={"type": "object"},
                        output_schema={"type": "object"},
                        handler=fail,
                    ),
                )
            ),
            allowlist=frozenset({"fixture.long_error"}),
        ),
        trace_store=TraceStore.open(tmp_path / "trace"),
        parent_context=parent_context,
        id_factory=factory,
        clock=lambda: FIXED_NOW,
    )

    with pytest.raises(RuntimeError):
        audited_gateway.execute("fixture.long_error", {})

    (record,) = audited_gateway.trace_store.find_by_trace_id(parent_context.trace_id)
    assert record.error_summary is not None
    assert len(record.error_summary) == 240
    assert record.error_summary.endswith("...")
