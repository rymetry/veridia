"""Validate skill outputs carried by a handoff envelope.

The envelope is the transport for **both** contract families (ADR-0010): each carried
artifact is validated against the schema its `schema_ref` names, whichever family owns
it. veridia does not copy or rewrite sqk-core's contracts
(`docs/plan/sqk-core-integration.md`); routing is by namespace
(`artifact_validator.schema_ref`).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from json_schema_errors import issue_from_error, relevant_errors
from jsonschema.exceptions import ValidationError

from artifact_validator.errors import ArtifactValidationError, ArtifactValidationIssue
from artifact_validator.schema_ref import validator_for_schema_ref
from artifact_validator.sqk_schema_store import HANDOFF_ENVELOPE_REF

ARTIFACTS_FIELD = "artifacts"
SCHEMA_REF_FIELD = "schema_ref"
ITEMS_FIELD = "items"
CONTENT_FIELD = "content"
ROOT_PATH = "$"


def validate_envelope_artifact(
    payload: Mapping[str, Any],
    *,
    schema_ref: str,
    path_prefix: str = ROOT_PATH,
) -> None:
    """Validate one sqk-core artifact against the schema named by `schema_ref`.

    Raises:
        SqkSchemaError: the schema is unavailable (missing submodule, unknown ref).
        ArtifactValidationError: the artifact does not satisfy the contract.
    """
    issues = _issues_for(payload, schema_ref=schema_ref, path_prefix=path_prefix)
    if issues:
        raise ArtifactValidationError(issues)


def validate_handoff_envelope(envelope: Mapping[str, Any]) -> None:
    """Validate a sqk-core handoff envelope and every artifact it carries.

    The envelope shape is checked first. When it fails, carried payloads are not
    checked: their JSONPaths would be reported against a structure that does not hold.

    Raises:
        SqkSchemaError: a declared `schema_ref` is unavailable.
        ArtifactValidationError: the envelope or one of its artifacts is invalid.
    """
    envelope_issues = _issues_for(
        envelope,
        schema_ref=HANDOFF_ENVELOPE_REF,
        path_prefix=ROOT_PATH,
    )
    if envelope_issues:
        raise ArtifactValidationError(envelope_issues)

    payload_issues = tuple(_envelope_payload_issues(envelope))
    if payload_issues:
        raise ArtifactValidationError(payload_issues)


def _envelope_payload_issues(envelope: Mapping[str, Any]) -> Iterator[ArtifactValidationIssue]:
    for index, artifact in enumerate(envelope[ARTIFACTS_FIELD]):
        schema_ref = artifact[SCHEMA_REF_FIELD]
        base_path = f"{ROOT_PATH}.{ARTIFACTS_FIELD}[{index}]"

        items = artifact.get(ITEMS_FIELD)
        if items is not None:
            for item_index, item in enumerate(items):
                yield from _issues_for(
                    item,
                    schema_ref=schema_ref,
                    path_prefix=f"{base_path}.{ITEMS_FIELD}[{item_index}]",
                )

        content = artifact.get(CONTENT_FIELD)
        if content is not None:
            yield from _issues_for(
                content,
                schema_ref=schema_ref,
                path_prefix=f"{base_path}.{CONTENT_FIELD}",
            )


def _issues_for(
    payload: Any,
    *,
    schema_ref: str,
    path_prefix: str,
) -> tuple[ArtifactValidationIssue, ...]:
    validator = validator_for_schema_ref(schema_ref)
    return tuple(
        _issue_with_prefix(error, path_prefix)
        for error in relevant_errors(validator.iter_errors(payload))
    )


def _issue_with_prefix(error: ValidationError, path_prefix: str) -> ArtifactValidationIssue:
    issue = issue_from_error(error)
    return ArtifactValidationIssue(
        field_path=_prefixed(issue.field_path, path_prefix),
        message=issue.message,
        schema_path=issue.schema_path,
        validator=issue.validator,
    )


def _prefixed(field_path: str, path_prefix: str) -> str:
    if path_prefix == ROOT_PATH:
        return field_path
    return f"{path_prefix}{field_path.removeprefix(ROOT_PATH)}"
