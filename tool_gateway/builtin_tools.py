"""Safe deterministic built-in tools for the Phase 0 Tool Gateway."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tool_gateway.registry import ToolDefinition, ToolRegistry

READ_TEXT_FILE = "repo.read_text_file"
LIST_FILES = "repo.list_files"
MAX_FILE_BYTES = 1_000_000

PATH_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["path"],
    "properties": {
        "path": {
            "type": "string",
            "minLength": 1,
        },
    },
    "additionalProperties": False,
}
READ_TEXT_FILE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["path", "content"],
    "properties": {
        "path": {"type": "string"},
        "content": {"type": "string"},
    },
    "additionalProperties": False,
}
LIST_FILES_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "minLength": 1,
            "default": ".",
        },
    },
    "additionalProperties": False,
}
LIST_FILES_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["path", "files"],
    "properties": {
        "path": {"type": "string"},
        "files": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def create_default_registry(repo_root: str | Path = ".") -> ToolRegistry:
    """Create the Phase 0 registry with read-only repository tools."""
    root = Path(repo_root).resolve()
    return ToolRegistry.from_definitions(
        (
            ToolDefinition(
                name=READ_TEXT_FILE,
                input_schema=PATH_INPUT_SCHEMA,
                output_schema=READ_TEXT_FILE_OUTPUT_SCHEMA,
                handler=lambda payload: _read_text_file(root, payload),
            ),
            ToolDefinition(
                name=LIST_FILES,
                input_schema=LIST_FILES_INPUT_SCHEMA,
                output_schema=LIST_FILES_OUTPUT_SCHEMA,
                handler=lambda payload: _list_files(root, payload),
            ),
        )
    )


def _read_text_file(repo_root: Path, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    relative_path = _relative_path(payload["path"])
    path = _resolve_inside_root(repo_root, relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"repo file does not exist: {relative_path.as_posix()}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"repo file exceeds {MAX_FILE_BYTES} bytes: {relative_path.as_posix()}")
    return {
        "path": relative_path.as_posix(),
        "content": path.read_text(encoding="utf-8"),
    }


def _list_files(repo_root: Path, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    relative_path = _relative_path(payload.get("path", "."))
    path = _resolve_inside_root(repo_root, relative_path)
    if not path.is_dir():
        raise NotADirectoryError(f"repo directory does not exist: {relative_path.as_posix()}")
    files = tuple(
        sorted(
            child.relative_to(repo_root).as_posix()
            for child in path.rglob("*")
            if child.is_file() and ".git" not in child.relative_to(repo_root).parts
        )
    )
    return {
        "path": relative_path.as_posix(),
        "files": list(files),
    }


def _relative_path(value: Any) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise ValueError("repo tool path must be relative")
    return path


def _resolve_inside_root(repo_root: Path, relative_path: Path) -> Path:
    path = (repo_root / relative_path).resolve()
    if not path.is_relative_to(repo_root):
        raise ValueError(f"repo tool path escapes repository root: {relative_path.as_posix()}")
    return path
