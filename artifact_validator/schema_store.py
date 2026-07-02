"""Load artifact schemas and route artifacts by artifact_type."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMA_GLOB = "*.schema.json"
ARTIFACT_BASE_SCHEMA = "artifact-base.schema.json"


@dataclass(frozen=True)
class SchemaEntry:
    artifact_type: str
    filename: str


@cache
def load_schema(filename: str) -> dict[str, Any]:
    return json.loads((SCHEMAS_DIR / filename).read_text(encoding="utf-8"))


@cache
def schema_registry() -> Registry:
    resources = [
        Resource.from_contents(load_schema(path.name))
        for path in sorted(SCHEMAS_DIR.glob(SCHEMA_GLOB))
    ]
    return Registry().with_resources((resource.contents["$id"], resource) for resource in resources)


@cache
def artifact_type_to_schema() -> dict[str, str]:
    entries = []
    for path in sorted(SCHEMAS_DIR.glob(SCHEMA_GLOB)):
        if path.name == ARTIFACT_BASE_SCHEMA:
            continue
        schema = load_schema(path.name)
        entries.append(
            SchemaEntry(
                artifact_type=schema["properties"]["artifact_type"]["const"],
                filename=path.name,
            )
        )
    return {entry.artifact_type: entry.filename for entry in entries}


@cache
def validator_for_artifact_type(artifact_type: str) -> Draft202012Validator:
    schema_filename = artifact_type_to_schema()[artifact_type]
    return Draft202012Validator(
        load_schema(schema_filename),
        registry=schema_registry(),
        format_checker=format_checker(),
    )


@cache
def format_checker() -> FormatChecker:
    checker = FormatChecker()

    @checker.checks("date-time")
    def is_timezone_aware_datetime(value: object) -> bool:
        if not isinstance(value, str):
            return True
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return parsed.tzinfo is not None and parsed.utcoffset() is not None

    return checker
