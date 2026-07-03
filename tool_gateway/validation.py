"""JSON Schema validation helpers for Tool Gateway payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from json_schema_errors import error_key, issue_from_error
from jsonschema import Draft202012Validator

from tool_gateway.errors import (
    ToolSchemaValidationError,
    ToolSchemaValidationIssue,
    ValidationDirection,
)


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
        _tool_issue_from_error(error)
        for error in sorted(validator.iter_errors(payload), key=error_key)
    )
    if issues:
        raise ToolSchemaValidationError(
            tool_name=tool_name,
            direction=direction,
            issues=issues,
        )


def _tool_issue_from_error(error: Any) -> ToolSchemaValidationIssue:
    issue = issue_from_error(error)
    return ToolSchemaValidationIssue(
        field_path=issue.field_path,
        message=issue.message,
        schema_path=issue.schema_path,
        validator=issue.validator,
    )
