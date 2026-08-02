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

from artifact_validator.schema_ref import load_schema

PATTERN_KEYWORD = "pattern"
PROPERTIES_KEYWORD = "properties"
ITEMS_KEYWORD = "items"
REF_KEYWORD = "$ref"
INTERNAL_REF_PREFIX = "#"
PATH_SEPARATOR = "/"


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
    yield from _walk(load_schema(schema_ref), name=None, schema_ref=schema_ref, seen={schema_ref})


def _walk(
    node: Any,
    *,
    name: str | None,
    schema_ref: str,
    seen: set[str],
) -> Iterator[tuple[str, str]]:
    if isinstance(node, list):
        for item in node:
            yield from _walk(item, name=name, schema_ref=schema_ref, seen=seen)
        return
    if not isinstance(node, dict):
        return

    pattern = node.get(PATTERN_KEYWORD)
    if isinstance(pattern, str) and name is not None:
        yield name, pattern

    yield from _walk_external_ref(node, name=name, schema_ref=schema_ref, seen=seen)

    for key, value in node.items():
        if key == PROPERTIES_KEYWORD and isinstance(value, dict):
            for prop_name, prop_schema in value.items():
                yield from _walk(prop_schema, name=prop_name, schema_ref=schema_ref, seen=seen)
        elif key == ITEMS_KEYWORD:
            # array items inherit the property name that owns the array
            yield from _walk(value, name=name, schema_ref=schema_ref, seen=seen)
        elif isinstance(value, dict | list):
            yield from _walk(value, name=name, schema_ref=schema_ref, seen=seen)


def _walk_external_ref(
    node: dict[str, Any],
    *,
    name: str | None,
    schema_ref: str,
    seen: set[str],
) -> Iterator[tuple[str, str]]:
    """Follow a `$ref` to another schema file in the same family.

    veridia schemas inherit ArtifactBase through `allOf: [{"$ref": "..."}]`, so a walk
    that stops at the reference never sees the inherited constraints — and the model is
    never told about them. That is the failure mode this module exists to prevent
    (learning-log 2026-08-02), so it must not reappear one indirection away.

    Internal refs (`#/$defs/...`) are skipped: the generic recursion already reaches
    them inside the same document.
    """
    target = node.get(REF_KEYWORD)
    if not isinstance(target, str) or target.startswith(INTERNAL_REF_PREFIX):
        return
    resolved = _sibling_ref(schema_ref, target)
    if resolved in seen:
        return
    seen.add(resolved)
    yield from _walk(load_schema(resolved), name=name, schema_ref=resolved, seen=seen)


def _sibling_ref(schema_ref: str, target: str) -> str:
    """Resolve a relative `$ref` filename against the referring schema's own ref.

    Both families name schemas by path, so replacing the last segment keeps the ref in
    the family it came from — routing never crosses families by accident (ADR-0010).
    """
    head, separator, _ = schema_ref.rpartition(PATH_SEPARATOR)
    return f"{head}{separator}{target}" if separator else target
