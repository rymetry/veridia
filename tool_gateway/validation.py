"""JSON Schema validation helpers for Tool Gateway payloads."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from tool_gateway.errors import (
    ToolSchemaValidationError,
    ToolSchemaValidationIssue,
    ValidationDirection,
)

REQUIRED_MESSAGE_RE = re.compile(r"^'(?P<field>[^']+)' is a required property$")


def validate_tool_payload(
    *,
    tool_name: str,
    direction: ValidationDirection,
    schema: Mapping[str, Any],
    payload: Any,
) -> None:
    """Validate a tool input or output payload against JSON Schema."""
    validator = Draft202012Validator(dict(schema))
    issues = tuple(
        _issue_from_error(error) for error in sorted(validator.iter_errors(payload), key=_error_key)
    )
    if issues:
        raise ToolSchemaValidationError(
            tool_name=tool_name,
            direction=direction,
            issues=issues,
        )


def _issue_from_error(error: ValidationError) -> ToolSchemaValidationIssue:
    return ToolSchemaValidationIssue(
        field_path=_field_path_for_error(error),
        message=error.message,
        schema_path=_path_to_jsonpath(error.schema_path),
        validator=str(error.validator),
    )


def _error_key(error: ValidationError) -> tuple[str, str, str]:
    return (_field_path_for_error(error), _path_to_jsonpath(error.schema_path), error.message)


def _field_path_for_error(error: ValidationError) -> str:
    if error.validator == "required":
        missing_field = _missing_required_field(error.message)
        if missing_field is not None:
            return _path_to_jsonpath([*error.path, missing_field])
    return _path_to_jsonpath(error.path)


def _missing_required_field(message: str) -> str | None:
    match = REQUIRED_MESSAGE_RE.match(message)
    if match is None:
        return None
    return match.group("field")


def _path_to_jsonpath(path: Any) -> str:
    rendered = "$"
    for segment in path:
        if isinstance(segment, int):
            rendered += f"[{segment}]"
        elif isinstance(segment, str) and segment.isidentifier():
            rendered += f".{segment}"
        else:
            rendered += f"[{segment!r}]"
    return rendered
