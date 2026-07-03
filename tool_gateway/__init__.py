"""Minimal Tool Gateway API for Phase 0."""

from tool_gateway.audit import AuditedToolGateway
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
from tool_gateway.redaction import REDACTION_MASK, redact_tool_args
from tool_gateway.registry import ToolDefinition, ToolHandler, ToolRegistry

__all__ = [
    "AuditedToolGateway",
    "LIST_FILES",
    "REDACTION_MASK",
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
    "redact_tool_args",
]
