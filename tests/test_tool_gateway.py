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


@pytest.mark.parametrize("payload", [{"path": "/etc/passwd"}, {"path": "../outside.txt"}])
def test_repo_read_text_file_rejects_absolute_and_parent_paths(
    tmp_path: Path,
    payload: dict[str, str],
) -> None:
    from tool_gateway import ToolExecutionError, ToolGateway, create_default_registry

    gateway = ToolGateway(
        registry=create_default_registry(tmp_path),
        allowlist=frozenset({"repo.read_text_file"}),
    )

    with pytest.raises(ToolExecutionError, match="relative|escapes"):
        gateway.execute("repo.read_text_file", payload)


def test_repo_read_text_file_rejects_symlink_escape(tmp_path: Path) -> None:
    from tool_gateway import ToolExecutionError, ToolGateway, create_default_registry

    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "escape.txt").symlink_to(outside)
    gateway = ToolGateway(
        registry=create_default_registry(repo),
        allowlist=frozenset({"repo.read_text_file"}),
    )

    with pytest.raises(ToolExecutionError, match="escapes"):
        gateway.execute("repo.read_text_file", {"path": "escape.txt"})


def test_repo_read_text_file_reports_missing_file(tmp_path: Path) -> None:
    from tool_gateway import ToolExecutionError, ToolGateway, create_default_registry

    gateway = ToolGateway(
        registry=create_default_registry(tmp_path),
        allowlist=frozenset({"repo.read_text_file"}),
    )

    with pytest.raises(ToolExecutionError, match="does not exist"):
        gateway.execute("repo.read_text_file", {"path": "missing.txt"})


def test_repo_read_text_file_rejects_files_over_size_limit(tmp_path: Path) -> None:
    from tool_gateway import ToolExecutionError, ToolGateway, create_default_registry
    from tool_gateway.builtin_tools import MAX_FILE_BYTES

    path = tmp_path / "huge.txt"
    path.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
    gateway = ToolGateway(
        registry=create_default_registry(tmp_path),
        allowlist=frozenset({"repo.read_text_file"}),
    )

    with pytest.raises(ToolExecutionError, match="exceeds"):
        gateway.execute("repo.read_text_file", {"path": "huge.txt"})


def test_repo_list_files_lists_files_and_ignores_git_directory(tmp_path: Path) -> None:
    from tool_gateway import ToolGateway, create_default_registry

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    gateway = ToolGateway(
        registry=create_default_registry(tmp_path),
        allowlist=frozenset({"repo.list_files"}),
    )

    assert gateway.execute("repo.list_files", {"path": "."}) == {
        "path": ".",
        "files": ["src/app.py"],
    }


def test_repo_list_files_reports_missing_directory(tmp_path: Path) -> None:
    from tool_gateway import ToolExecutionError, ToolGateway, create_default_registry

    gateway = ToolGateway(
        registry=create_default_registry(tmp_path),
        allowlist=frozenset({"repo.list_files"}),
    )

    with pytest.raises(ToolExecutionError, match="directory does not exist"):
        gateway.execute("repo.list_files", {"path": "missing"})


def test_registry_rejects_duplicate_tool_names() -> None:
    from tool_gateway import ToolDefinition, ToolRegistry

    definition = ToolDefinition(
        name="fixture.echo",
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        handler=lambda _payload: {},
    )

    with pytest.raises(ValueError, match="duplicate"):
        ToolRegistry.from_definitions((definition, definition))


def test_registry_rejects_unregistered_tool_name() -> None:
    from tool_gateway import ToolNotRegisteredError, ToolRegistry

    registry = ToolRegistry.from_definitions(())

    with pytest.raises(ToolNotRegisteredError, match="missing.tool"):
        registry.get("missing.tool")


def test_gateway_wraps_handler_exception() -> None:
    from tool_gateway import ToolDefinition, ToolExecutionError, ToolGateway, ToolRegistry

    def fail(_payload: object) -> dict[str, object]:
        raise RuntimeError("boom")

    gateway = ToolGateway(
        registry=ToolRegistry.from_definitions(
            (
                ToolDefinition(
                    name="fixture.fail",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                    handler=fail,
                ),
            )
        ),
        allowlist=frozenset({"fixture.fail"}),
    )

    with pytest.raises(ToolExecutionError, match="fixture.fail.*boom"):
        gateway.execute("fixture.fail", {})


def test_validation_error_paths_include_missing_required_field_and_array_index() -> None:
    from tool_gateway import ToolSchemaValidationError
    from tool_gateway.validation import validate_tool_payload

    schema = {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {"name": {"type": "string"}},
                },
            }
        },
    }

    with pytest.raises(ToolSchemaValidationError) as exc_info:
        validate_tool_payload(
            tool_name="fixture.validate",
            direction="input",
            schema=schema,
            payload={"items": [{}]},
        )

    assert exc_info.value.issues[0].field_path == "$.items[0].name"
