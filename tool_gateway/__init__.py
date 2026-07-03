"""Minimal Tool Gateway API for Phase 0."""

from tool_gateway.builtin_tools import LIST_FILES, READ_TEXT_FILE, create_default_registry
from tool_gateway.errors import (
    ToolExecutionError,
    ToolGatewayError,
    ToolNotAllowedError,
    ToolNotRegisteredError,
    ToolSchemaValidationError,
    ToolSchemaValidationIssue,
)
from tool_gateway.gateway import ToolGateway
from tool_gateway.registry import ToolDefinition, ToolHandler, ToolRegistry

__all__ = [
    "LIST_FILES",
    "READ_TEXT_FILE",
    "ToolDefinition",
    "ToolExecutionError",
    "ToolGateway",
    "ToolGatewayError",
    "ToolHandler",
    "ToolNotAllowedError",
    "ToolNotRegisteredError",
    "ToolRegistry",
    "ToolSchemaValidationError",
    "ToolSchemaValidationIssue",
    "create_default_registry",
]
