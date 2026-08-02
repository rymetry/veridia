"""Load sqk-core skill I/O schemas (`vendor/sqk-core/schemas`) for boundary validation.

sqk-core schemas are the canonical contracts for the test process artifacts
(TRA / TAD / TDD outputs). They intentionally carry no `artifact_type` and set
`additionalProperties: false`, so they cannot be routed by the veridia
`artifact_type` registry (`artifact_validator.schema_store`). They are routed by
the `schema_ref` that a sqk-core `handoff-envelope` declares for each artifact.

The sqk-core submodule may be absent (fresh clone without
`git submodule update --init`). Every entry point fails loudly with the fix
rather than resolving to an empty schema set.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from artifact_validator.errors import SqkSchemaError
from artifact_validator.schema_store import format_checker

SQK_ROOT = Path(__file__).resolve().parent.parent / "vendor" / "sqk-core"
SQK_SCHEMAS_DIR = SQK_ROOT / "schemas"
SCHEMA_GLOB = "*.schema.json"
SCHEMA_REF_PREFIX = "schemas/"
HANDOFF_ENVELOPE_REF = "schemas/handoff-envelope.schema.json"
SUBMODULE_HINT = "git submodule update --init --recursive"


def available_schema_refs() -> tuple[str, ...]:
    """Return every loadable `schema_ref`, sorted.

    Not cached: the submodule can be checked out after this process starts.
    """
    if not SQK_SCHEMAS_DIR.is_dir():
        return ()
    return tuple(
        sorted(f"{SCHEMA_REF_PREFIX}{path.name}" for path in SQK_SCHEMAS_DIR.glob(SCHEMA_GLOB))
    )


def resolve_schema_path(schema_ref: str) -> Path:
    """Map a sqk-core `schema_ref` to a file under `vendor/sqk-core/schemas`.

    Raises:
        SqkSchemaError: submodule missing, ref outside the schema directory, or unknown ref.
    """
    refs = available_schema_refs()
    if not refs:
        raise SqkSchemaError(
            f"sqk-core schemas not found under {SQK_SCHEMAS_DIR}. "
            f"the submodule is not checked out: run `{SUBMODULE_HINT}`"
        )
    if not schema_ref.startswith(SCHEMA_REF_PREFIX):
        raise SqkSchemaError(f"schema_ref must start with {SCHEMA_REF_PREFIX!r}: {schema_ref!r}")

    candidate = (SQK_ROOT / schema_ref).resolve()
    schemas_dir = SQK_SCHEMAS_DIR.resolve()
    if not candidate.is_relative_to(schemas_dir):
        raise SqkSchemaError(f"schema_ref escapes the sqk-core schema directory: {schema_ref!r}")
    if not candidate.is_file():
        supported = ", ".join(refs)
        raise SqkSchemaError(f"unknown schema_ref {schema_ref!r}; supported: {supported}")
    return candidate


@cache
def load_schema(schema_ref: str) -> dict[str, Any]:
    """Read and parse one sqk-core schema by `schema_ref`."""
    path = resolve_schema_path(schema_ref)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SqkSchemaError(f"failed to parse sqk-core schema {schema_ref}: {exc}") from exc


@cache
def schema_registry() -> Registry:
    """Build a `$ref` registry over every available sqk-core schema."""
    resources = [
        Resource.from_contents(load_schema(schema_ref)) for schema_ref in available_schema_refs()
    ]
    return Registry().with_resources((resource.contents["$id"], resource) for resource in resources)


@cache
def validator_for_schema_ref(schema_ref: str) -> Draft202012Validator:
    """Return the validator for one sqk-core `schema_ref`."""
    return Draft202012Validator(
        load_schema(schema_ref),
        registry=schema_registry(),
        format_checker=format_checker(),
    )
