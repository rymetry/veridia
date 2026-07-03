"""T-015 Tool Gateway minimal contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_executes_allowlisted_registered_tool(tmp_path: Path) -> None:
    from tool_gateway import ToolGateway, create_default_registry

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# Synthetic repo\n", encoding="utf-8")
    gateway = ToolGateway(
        registry=create_default_registry(repo_root),
        allowlist=frozenset({"repo.read_text_file"}),
    )

    result = gateway.execute("repo.read_text_file", {"path": "README.md"})

    assert result == {
        "path": "README.md",
        "content": "# Synthetic repo\n",
    }


def test_rejects_tool_outside_allowlist(tmp_path: Path) -> None:
    from tool_gateway import ToolGateway, ToolNotAllowedError, create_default_registry

    gateway = ToolGateway(
        registry=create_default_registry(tmp_path),
        allowlist=frozenset({"repo.list_files"}),
    )

    with pytest.raises(ToolNotAllowedError, match="repo.read_text_file"):
        gateway.execute("repo.read_text_file", {"path": "README.md"})


def test_rejects_input_schema_violation(tmp_path: Path) -> None:
    from tool_gateway import ToolGateway, ToolSchemaValidationError, create_default_registry

    gateway = ToolGateway(
        registry=create_default_registry(tmp_path),
        allowlist=frozenset({"repo.read_text_file"}),
    )

    with pytest.raises(ToolSchemaValidationError) as exc_info:
        gateway.execute("repo.read_text_file", {"path": 123})

    error = exc_info.value
    assert error.tool_name == "repo.read_text_file"
    assert error.direction == "input"
    assert error.issues[0].field_path == "$.path"


def test_rejects_output_schema_violation() -> None:
    from tool_gateway import (
        ToolDefinition,
        ToolGateway,
        ToolRegistry,
        ToolSchemaValidationError,
    )

    registry = ToolRegistry.from_definitions(
        (
            ToolDefinition(
                name="fixture.bad_output",
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "required": ["ok"],
                    "properties": {"ok": {"type": "boolean"}},
                    "additionalProperties": False,
                },
                handler=lambda _payload: {"ok": "yes"},
            ),
        )
    )
    gateway = ToolGateway(
        registry=registry,
        allowlist=frozenset({"fixture.bad_output"}),
    )

    with pytest.raises(ToolSchemaValidationError) as exc_info:
        gateway.execute("fixture.bad_output", {})

    error = exc_info.value
    assert error.tool_name == "fixture.bad_output"
    assert error.direction == "output"
    assert error.issues[0].field_path == "$.ok"
