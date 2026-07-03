"""Artifact validation API."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from json_schema_errors import error_key, issue_from_error
from jsonschema.exceptions import ValidationError

from artifact_validator.errors import ArtifactValidationError, ArtifactValidationIssue
from artifact_validator.schema_store import artifact_type_to_schema, validator_for_artifact_type

ARTIFACT_TYPE_FIELD = "artifact_type"


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
        _artifact_issue_from_error(error)
        for error in _relevant_errors(validator.iter_errors(artifact))
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
        raise ValueError(f"artifact JSON must be an object: {artifact_path}")
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


def _artifact_issue_from_error(error: ValidationError) -> ArtifactValidationIssue:
    issue = issue_from_error(error)
    return ArtifactValidationIssue(
        field_path=issue.field_path,
        message=issue.message,
        schema_path=issue.schema_path,
        validator=issue.validator,
    )


def _relevant_errors(errors: Any) -> tuple[ValidationError, ...]:
    all_errors = tuple(errors)
    specific_errors = tuple(
        error for error in all_errors if error.validator != "unevaluatedProperties"
    )
    if specific_errors:
        return tuple(sorted(specific_errors, key=error_key))
    return tuple(sorted(all_errors, key=error_key))
