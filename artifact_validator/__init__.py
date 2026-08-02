"""Reusable artifact JSON validator for veridia's contract boundaries.

Two schema families are validated here and they are routed differently:

- **by `artifact_type`** — veridia contracts (`schemas/*.schema.json`) inherit
  `ArtifactBase` (with the documented exceptions in `schemas/README.md`).
  Use `validate_artifact` / `validate_artifact_file`.
- **by `schema_ref`** — artifacts carried inside a handoff envelope. Both families
  ride the same envelope (ADR-0010) and are routed by namespace:
  `schemas/…` is sqk-core, `veridia://schemas/…` is veridia. There is no fallback
  between them. Use `validate_handoff_envelope` / `validate_envelope_artifact`.

sqk-core schemas carry no `artifact_type` and are `additionalProperties: false`, so
they can only be reached through the `schema_ref` route.
"""

from artifact_validator.errors import (
    ArtifactValidationError,
    ArtifactValidationIssue,
    SqkSchemaError,
)
from artifact_validator.schema_ref import (
    FAMILY_SQK_CORE,
    FAMILY_VERIDIA,
    VERIDIA_REF_PREFIX,
    declares_sqk_core_contract,
    family_of,
    veridia_ref_for,
)
from artifact_validator.sqk_validator import validate_envelope_artifact, validate_handoff_envelope
from artifact_validator.validator import validate_artifact, validate_artifact_file

__all__ = [
    "FAMILY_SQK_CORE",
    "FAMILY_VERIDIA",
    "VERIDIA_REF_PREFIX",
    "ArtifactValidationError",
    "ArtifactValidationIssue",
    "SqkSchemaError",
    "declares_sqk_core_contract",
    "family_of",
    "validate_artifact",
    "validate_artifact_file",
    "validate_envelope_artifact",
    "validate_handoff_envelope",
    "veridia_ref_for",
]
