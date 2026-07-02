"""Validation error types with machine-readable paths."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactValidationIssue:
    """One schema validation failure."""

    field_path: str
    message: str
    schema_path: str
    validator: str

    def to_dict(self) -> dict[str, str]:
        return {
            "field_path": self.field_path,
            "message": self.message,
            "schema_path": self.schema_path,
            "validator": self.validator,
        }


class ArtifactValidationError(ValueError):
    """Raised when an artifact fails contract validation."""

    def __init__(self, errors: tuple[ArtifactValidationIssue, ...]) -> None:
        self.errors = errors
        super().__init__(self._build_message(errors))

    def to_dict(self) -> dict[str, list[dict[str, str]]]:
        return {"errors": [issue.to_dict() for issue in self.errors]}

    @staticmethod
    def _build_message(errors: tuple[ArtifactValidationIssue, ...]) -> str:
        return "; ".join(f"{issue.field_path}: {issue.message}" for issue in errors)
