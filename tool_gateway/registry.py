"""Tool definition and registry types."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from tool_gateway.errors import ToolNotRegisteredError

ToolHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class ToolDefinition:
    """Registered tool contract and implementation."""

    name: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any]
    handler: ToolHandler

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("tool name must be non-empty")


@dataclass(frozen=True)
class ToolRegistry:
    """Immutable lookup table for tool definitions."""

    _definitions: Mapping[str, ToolDefinition]

    @classmethod
    def from_definitions(cls, definitions: tuple[ToolDefinition, ...]) -> ToolRegistry:
        by_name: dict[str, ToolDefinition] = {}
        for definition in definitions:
            if definition.name in by_name:
                raise ValueError(f"duplicate tool definition: {definition.name}")
            by_name[definition.name] = definition
        return cls(_definitions=MappingProxyType(by_name))

    def get(self, tool_name: str) -> ToolDefinition:
        try:
            return self._definitions[tool_name]
        except KeyError as exc:
            raise ToolNotRegisteredError(tool_name) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))
