"""The CLI-facing output schema for a sqk-core handoff envelope.

ADR-0005 Decision 6.1: only a conservative portable profile of JSON Schema keywords is
assumed to constrain both backends (`type` / `properties` / `required` / `enum` /
`items` / `additionalProperties`). sqk-core's `handoff-envelope.schema.json` uses
`oneOf` for `assumptions[]`, which is outside that profile.

So the model is constrained by this profile-safe shape, and the response is then
validated against the real sqk-core contract by `artifact_validator`. Enforcement never
weakens: it moves from the CLI to the validator.
"""

from __future__ import annotations

from typing import Any

GATE_STATUSES = ("passed", "passed-with-risks", "blocked")


def portable_envelope_schema(schema_ref_enum: tuple[str, ...]) -> dict[str, Any]:
    """Return a portable-profile schema for one skill's expected envelope.

    `schema_ref_enum` pins `artifacts[].schema_ref` to the refs the skill declares, so a
    model cannot invent a contract it then trivially satisfies.
    """
    artifact: dict[str, Any] = {
        "type": "object",
        "properties": {
            "type": {"type": "string"},
            "schema_ref": {"type": "string"},
            "items": {"type": "array", "items": {"type": "object"}},
            "content": {"type": "object"},
        },
        "required": ["type", "schema_ref"],
        "additionalProperties": False,
    }
    if schema_ref_enum:
        artifact["properties"]["schema_ref"] = {"type": "string", "enum": list(schema_ref_enum)}

    return {
        "type": "object",
        "properties": {
            "source_skill": {"type": "string"},
            "phase": {"type": "string"},
            "artifacts": {"type": "array", "items": artifact},
            "trace_ids": {"type": "array", "items": {"type": "string"}},
            # sqk-core allows string | object here; the portable profile cannot express a
            # union, so the model is asked for the string form and the validator accepts both
            "assumptions": {"type": "array", "items": {"type": "string"}},
            "open_questions": {"type": "array", "items": {"type": "string"}},
            "gate_status": {"type": "string", "enum": list(GATE_STATUSES)},
        },
        "required": [
            "source_skill",
            "phase",
            "artifacts",
            "trace_ids",
            "assumptions",
            "open_questions",
            "gate_status",
        ],
        "additionalProperties": False,
    }
