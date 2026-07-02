"""Artifact validation API."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema.exceptions import ValidationError

from artifact_validator.errors import ArtifactValidationError, ArtifactValidationIssue
from artifact_validator.schema_store import artifact_type_to_schema, validator_for_artifact_type

ARTIFACT_TYPE_FIELD = "artifact_type"
REQUIRED_MESSAGE_RE = re.compile(r"^'(?P<field>[^']+)' is a required property$")


def validate_artifact(artifact: Mapping[str, Any]) -> None:
    """Validate one artifact dict against the schema selected by artifact_type.

    Raises:
        ArtifactValidationError: the artifact does not satisfy the selected contract.
    """
    artifact_type = artifact.get(ARTIFACT_TYPE_FIELD)
    routing_issue = _artifact_type_issue(artifact_type)
    if routing_issue is not None:
        raise ArtifactValidationError((routing_issue,))

    validator = validator_for_artifact_type(artifact_type)
    issues = tuple(
        _issue_from_error(error) for error in _relevant_errors(validator.iter_errors(artifact))
    )
    if issues:
        raise ArtifactValidationError(issues)


def validate_artifact_file(path: str | Path) -> None:
    """Read and validate one JSON artifact file."""
    artifact_path = Path(path)
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"failed to read artifact file {artifact_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to parse artifact file {artifact_path}: {exc}") from exc

    if not isinstance(artifact, Mapping):
        issue = ArtifactValidationIssue(
            field_path="$",
            message="artifact JSON must be an object",
            schema_path="$",
            validator="type",
        )
        raise ArtifactValidationError((issue,))
    validate_artifact(artifact)


def _artifact_type_issue(artifact_type: Any) -> ArtifactValidationIssue | None:
    if artifact_type is None:
        return ArtifactValidationIssue(
            field_path="$.artifact_type",
            message="'artifact_type' is a required property",
            schema_path="$.required",
            validator="required",
        )
    if not isinstance(artifact_type, str):
        return ArtifactValidationIssue(
            field_path="$.artifact_type",
            message="artifact_type must be a string",
            schema_path="$.properties.artifact_type.type",
            validator="type",
        )
    known_types = artifact_type_to_schema()
    if artifact_type not in known_types:
        supported = ", ".join(sorted(known_types))
        return ArtifactValidationIssue(
            field_path="$.artifact_type",
            message=f"unknown artifact_type {artifact_type!r}; supported: {supported}",
            schema_path="$.properties.artifact_type.const",
            validator="artifact_type",
        )
    return None


def _issue_from_error(error: ValidationError) -> ArtifactValidationIssue:
    return ArtifactValidationIssue(
        field_path=_field_path_for_error(error),
        message=error.message,
        schema_path=_path_to_jsonpath(error.schema_path),
        validator=str(error.validator),
    )


def _relevant_errors(errors: Any) -> tuple[ValidationError, ...]:
    all_errors = tuple(errors)
    specific_errors = tuple(
        error for error in all_errors if error.validator != "unevaluatedProperties"
    )
    if specific_errors:
        return tuple(sorted(specific_errors, key=_error_key))
    return tuple(sorted(all_errors, key=_error_key))


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
