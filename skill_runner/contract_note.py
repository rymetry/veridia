"""Tell the model the constraints the validator will enforce but the CLI cannot.

ADR-0005 Decision 6.1 keeps the CLI-facing schema inside a portable profile, so
keywords like `pattern` never reach the backend. Enforcement still happens — in
`artifact_validator` — which means a model that is not told about them produces output
that is rejected after the call is paid for.

Observed cold-start failure (2026-08-02): `test-architecture-design` synthesised
`DTC-A01` / `DTC-B02` style grouping IDs, which are rejected by sqk-core's
`^DTC-[0-9]+$`. The constraints are therefore derived from the very schemas the
validator uses and appended to the instruction half of the prompt. Nothing is
hardcoded: if sqk-core changes an ID convention, this note changes with it.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

from artifact_validator.sqk_schema_store import load_schema

PATTERN_KEYWORD = "pattern"
PROPERTIES_KEYWORD = "properties"
ITEMS_KEYWORD = "items"


def contract_note(schema_refs: Sequence[str]) -> str:
    """Render the non-portable constraints of the declared output schemas as text.

    Returns an empty string when the schemas carry no such constraint.
    """
    constraints = sorted(
        {(name, pattern) for ref in schema_refs for name, pattern in _patterns(ref)}
    )
    if not constraints:
        return ""
    lines = "\n".join(
        f"- `{name}` は正規表現 `{pattern}` に一致すること" for name, pattern in constraints
    )
    return (
        "## 出力契約(検証される制約)\n\n"
        "出力は下記の制約で機械検証され、違反した場合は破棄される。"
        "上流成果物が無くIDを新規に採番する場合も、この形式に従うこと"
        "(接尾辞にアルファベットを足す等の独自採番をしない)。\n\n"
        f"{lines}\n"
    )


def _patterns(schema_ref: str) -> Iterator[tuple[str, str]]:
    """Yield (property name, pattern) for every `pattern` constraint in one schema."""
    yield from _walk(load_schema(schema_ref), name=None)


def _walk(node: Any, *, name: str | None) -> Iterator[tuple[str, str]]:
    if isinstance(node, dict):
        pattern = node.get(PATTERN_KEYWORD)
        if isinstance(pattern, str) and name is not None:
            yield name, pattern
        for key, value in node.items():
            if key == PROPERTIES_KEYWORD and isinstance(value, dict):
                for prop_name, prop_schema in value.items():
                    yield from _walk(prop_schema, name=prop_name)
            elif key == ITEMS_KEYWORD:
                # array items inherit the property name that owns the array
                yield from _walk(value, name=name)
            elif isinstance(value, dict | list):
                yield from _walk(value, name=name)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item, name=name)
