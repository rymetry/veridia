"""Tool Gateway error types with machine-readable validation details."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ValidationDirection = Literal["input", "output"]


class ToolGatewayError(Exception):
    """Base error for Tool Gateway failures."""


class ToolNotAllowedError(ToolGatewayError, PermissionError):
    """Raised when a tool is not present in the gateway allowlist."""

    def __init__(self, tool_name: str, allowed_tools: tuple[str, ...]) -> None:
        self.tool_name = tool_name
        self.allowed_tools = allowed_tools
        super().__init__(f"tool {tool_name!r} is not allowed")


class ToolNotRegisteredError(ToolGatewayError, LookupError):
    """Raised when an allowlisted tool has no registered implementation."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"tool {tool_name!r} is not registered")


class ToolExecutionError(ToolGatewayError, RuntimeError):
    """Raised when a registered tool callable fails."""

    def __init__(self, tool_name: str, cause: Exception) -> None:
        self.tool_name = tool_name
        super().__init__(f"tool {tool_name!r} failed during execution: {cause}")


@dataclass(frozen=True)
class ToolSchemaValidationIssue:
    """One JSON Schema validation failure for a tool payload."""

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


class ToolSchemaValidationError(ToolGatewayError, ValueError):
    """Raised when a tool input or output violates its JSON Schema."""

    def __init__(
        self,
        *,
        tool_name: str,
        direction: ValidationDirection,
        issues: tuple[ToolSchemaValidationIssue, ...],
    ) -> None:
        self.tool_name = tool_name
        self.direction = direction
        self.issues = issues
        super().__init__(self._build_message(tool_name, direction, issues))

    def to_dict(self) -> dict[str, str | list[dict[str, str]]]:
        return {
            "tool_name": self.tool_name,
            "direction": self.direction,
            "errors": [issue.to_dict() for issue in self.issues],
        }

    @staticmethod
    def _build_message(
        tool_name: str,
        direction: ValidationDirection,
        issues: tuple[ToolSchemaValidationIssue, ...],
    ) -> str:
        details = "; ".join(f"{issue.field_path}: {issue.message}" for issue in issues)
        return f"{tool_name} {direction} schema validation failed: {details}"
