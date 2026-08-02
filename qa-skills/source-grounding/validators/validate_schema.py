"""Template validator for input/output JSON Schema contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise TypeError(f"JSON object expected: {path}")
    return loaded


def validate_instance(schema_path: Path, instance_path: Path) -> None:
    """Validate an instance file against a schema file."""
    Draft202012Validator(load_json(schema_path)).validate(load_json(instance_path))
