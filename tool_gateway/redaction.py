"""Redaction helpers for Tool Gateway audit records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

REDACTION_MASK = "<redacted>"
SECRET_KEY_PARTS = (
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "password",
    "secret",
    "token",
)


def redact_tool_args(args: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-compatible copy with secret-like argument values masked."""
    return {key: _redact_value(key, value) for key, value in args.items()}


def sensitive_values(args: Mapping[str, Any]) -> tuple[str, ...]:
    """Collect string values masked by `redact_tool_args` for summary cleanup."""
    collected: list[str] = []
    _collect_sensitive_values(args, collected)
    return tuple(collected)


def _redact_value(key: object, value: Any) -> Any:
    if _is_secret_key(key):
        return REDACTION_MASK
    if isinstance(value, Mapping):
        return {
            child_key: _redact_value(child_key, child_value)
            for child_key, child_value in value.items()
        }
    if _is_sequence(value):
        return [_redact_sequence_item(item) for item in value]
    return value


def _redact_sequence_item(item: Any) -> Any:
    if isinstance(item, Mapping):
        return {key: _redact_value(key, value) for key, value in item.items()}
    if _is_sequence(item):
        return [_redact_sequence_item(child) for child in item]
    return item


def _collect_sensitive_values(
    value: Any,
    collected: list[str],
    parent_key: object | None = None,
) -> None:
    if _is_secret_key(parent_key):
        if isinstance(value, str) and value:
            collected.append(value)
        return
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            _collect_sensitive_values(child_value, collected, child_key)
        return
    if _is_sequence(value):
        for item in value:
            _collect_sensitive_values(item, collected, parent_key)


def _is_secret_key(key: object | None) -> bool:
    if key is None:
        return False
    normalized = str(key).lower().replace("-", "_")
    return any(part in normalized for part in SECRET_KEY_PARTS)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray)
