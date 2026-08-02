"""Where a source's trust label is decided (ADR-0009 Decision 2).

The label lives here, in the ingestion boundary, and not in the skill that reads the
source. A schema can pin the value domain but not who supplied the value: if the same
party both writes the trust label and is trusted because of it, the gate is
self-certified and can be walked around (learning-log 2026-08-02).

The allowed values are read from the SourceMap schema rather than restated, so the
two cannot drift apart.
"""

from __future__ import annotations

from functools import cache

from artifact_validator.schema_store import load_schema

from source_connector.errors import TrustLevelError

SOURCE_MAP_SCHEMA = "source-map.schema.json"
TRUST_LEVEL_FIELD = "trust_level"
# Pointing the configuration at a repository is itself the act of trusting it.
DEFAULT_TRUST_LEVEL = "trusted"


@cache
def trust_levels() -> tuple[str, ...]:
    """The trust labels the SourceMap contract allows, in schema order."""
    schema = load_schema(SOURCE_MAP_SCHEMA)
    return tuple(schema["properties"][TRUST_LEVEL_FIELD]["enum"])


def validate_trust_level(value: str) -> str:
    """Check a trust label against the contract.

    Raises:
        TrustLevelError: the label is not one the SourceMap contract allows.
    """
    allowed = trust_levels()
    if value not in allowed:
        raise TrustLevelError(
            f"unknown trust level {value!r}; the SourceMap contract allows: {', '.join(allowed)}"
        )
    return value
