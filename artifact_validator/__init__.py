"""Reusable artifact JSON validator for Phase 0 artifact contracts.

Two schema families are validated here and they are routed differently:

- veridia contracts (`schemas/*.schema.json`) carry `artifact_type` and inherit
  `ArtifactBase`. Use `validate_artifact` / `validate_artifact_file`.
- sqk-core skill I/O contracts (`vendor/sqk-core/schemas/*.schema.json`) carry no
  `artifact_type` and are `additionalProperties: false`. They are routed by the
  `schema_ref` a handoff envelope declares. Use `validate_handoff_envelope` /
  `validate_sqk_artifact`.
"""

from artifact_validator.errors import (
    ArtifactValidationError,
    ArtifactValidationIssue,
    SqkSchemaError,
)
from artifact_validator.sqk_validator import validate_handoff_envelope, validate_sqk_artifact
from artifact_validator.validator import validate_artifact, validate_artifact_file

__all__ = [
    "ArtifactValidationError",
    "ArtifactValidationIssue",
    "SqkSchemaError",
    "validate_artifact",
    "validate_artifact_file",
    "validate_handoff_envelope",
    "validate_sqk_artifact",
]
