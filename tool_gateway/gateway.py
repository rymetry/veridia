"""Tool Gateway execution boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from tool_gateway.errors import ToolExecutionError, ToolNotAllowedError
from tool_gateway.registry import ToolRegistry
from tool_gateway.validation import validate_tool_payload


@dataclass(frozen=True)
class ToolGateway:
    """Execute registered tools only after allowlist and schema checks."""

    registry: ToolRegistry
    allowlist: frozenset[str]

    def execute(self, tool_name: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Run one tool call through the Phase 0 Gateway boundary.

        T-016 can wrap this boundary to record started/ended/error events without
        changing individual tool callables.
        """
        if tool_name not in self.allowlist:
            raise ToolNotAllowedError(tool_name, tuple(sorted(self.allowlist)))

        definition = self.registry.get(tool_name)
        validate_tool_payload(
            tool_name=tool_name,
            direction="input",
            schema=definition.input_schema,
            payload=payload,
        )
        try:
            result = definition.handler(payload)
        except Exception as exc:
            raise ToolExecutionError(tool_name, exc) from exc

        validate_tool_payload(
            tool_name=tool_name,
            direction="output",
            schema=definition.output_schema,
            payload=result,
        )
        return result
