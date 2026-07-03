"""Shared JSON Schema validation issue formatting helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jsonschema.exceptions import ValidationError

REQUIRED_MESSAGE_RE = re.compile(r"^'(?P<field>[^']+)' is a required property$")


@dataclass(frozen=True)
class JsonSchemaIssue:
    """One formatted JSON Schema validation issue."""

    field_path: str
    message: str
    schema_path: str
    validator: str


def issue_from_error(error: ValidationError) -> JsonSchemaIssue:
    """Return a machine-readable issue from a jsonschema ValidationError."""
    return JsonSchemaIssue(
        field_path=field_path_for_error(error),
        message=error.message,
        schema_path=path_to_jsonpath(error.schema_path),
        validator=str(error.validator),
    )


def error_key(error: ValidationError) -> tuple[str, str, str]:
    """Stable sort key for JSON Schema errors."""
    return (field_path_for_error(error), path_to_jsonpath(error.schema_path), error.message)


def field_path_for_error(error: ValidationError) -> str:
    """Return the instance JSONPath for an error, including missing required fields."""
    if error.validator == "required":
        missing_field = missing_required_field(error.message)
        if missing_field is not None:
            return path_to_jsonpath([*error.path, missing_field])
    return path_to_jsonpath(error.path)


def missing_required_field(message: str) -> str | None:
    """Extract the missing required field name from jsonschema's message."""
    match = REQUIRED_MESSAGE_RE.match(message)
    if match is None:
        return None
    return match.group("field")


def path_to_jsonpath(path: Any) -> str:
    """Render jsonschema path/schema_path segments as a simple JSONPath string."""
    rendered = "$"
    for segment in path:
        if isinstance(segment, int):
            rendered += f"[{segment}]"
        elif isinstance(segment, str) and segment.isidentifier():
            rendered += f".{segment}"
        else:
            rendered += f"[{segment!r}]"
    return rendered
