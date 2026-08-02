"""Project a contract schema into the portable profile the CLI backends accept.

ADR-0005 Decision 6.1 keeps the CLI-facing schema inside a conservative profile
(`type` / `properties` / `required` / `enum` / `items` / `additionalProperties`), and
enforcement stays with `artifact_validator`. Until now the envelope handed the model
`content: {"type": "object"}` — the model was told *nothing* about the artifact it had
to produce.

Observed cost of that (2026-08-02, real run against PR #14): the model omitted six
ArtifactBase fields, invented `label` / `note` on items, and used a `source_type`
outside the enum. Every one of those is expressible **inside** the portable profile, so
none of it needed to happen.

What the projection does:

- inlines `$ref` (sibling file and internal `#/$defs/...`) and flattens `allOf`, so an
  inherited contract arrives as one self-contained shape
- rewrites `const: X` as `enum: [X]` — same meaning, and `enum` is in the profile
- rewrites `unevaluatedProperties: false` as `additionalProperties: false`, which is
  equivalent once inheritance is inlined and closes the object the model sees
- drops everything else (`pattern`, `minLength`, `format`, `description`, …). `pattern`
  still reaches the model through `contract_note`; the rest is enforced by the
  validator alone.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from artifact_validator.schema_ref import load_schema, sibling_ref

PORTABLE_KEYWORDS = ("type", "properties", "required", "enum", "items", "additionalProperties")
REF_KEYWORD = "$ref"
ALL_OF_KEYWORD = "allOf"
CONST_KEYWORD = "const"
UNEVALUATED_KEYWORD = "unevaluatedProperties"
INTERNAL_REF_PREFIX = "#"
COMPOSITION_KEYWORDS = frozenset({REF_KEYWORD, ALL_OF_KEYWORD})


def portable_projection(schema_ref: str) -> dict[str, Any]:
    """Return the portable-profile shape of the contract `schema_ref` names."""
    document = load_schema(schema_ref)
    return _project(document, document=document, schema_ref=schema_ref, seen=frozenset())


def _project(
    node: Any,
    *,
    document: Mapping[str, Any],
    schema_ref: str,
    seen: frozenset[str],
) -> dict[str, Any]:
    """Flatten composition, then keep only what the portable profile allows."""
    if not isinstance(node, Mapping):
        return {}
    flat = _flattened(node, document=document, schema_ref=schema_ref, seen=seen)
    projected: dict[str, Any] = {}

    for keyword in PORTABLE_KEYWORDS:
        if keyword not in flat:
            continue
        value = flat[keyword]
        if keyword == "properties" and isinstance(value, Mapping):
            projected[keyword] = {
                name: _project(subschema, document=document, schema_ref=schema_ref, seen=seen)
                for name, subschema in value.items()
            }
        elif keyword == "items":
            projected[keyword] = _project(
                value, document=document, schema_ref=schema_ref, seen=seen
            )
        else:
            projected[keyword] = value

    if CONST_KEYWORD in flat and "enum" not in projected:
        projected["enum"] = [flat[CONST_KEYWORD]]
    if flat.get(UNEVALUATED_KEYWORD) is False:
        projected["additionalProperties"] = False
    return projected


def _flattened(
    node: Mapping[str, Any],
    *,
    document: Mapping[str, Any],
    schema_ref: str,
    seen: frozenset[str],
) -> dict[str, Any]:
    """Merge `$ref` targets and `allOf` members into one mapping, child last."""
    merged: dict[str, Any] = {}
    for part in _parts(node, document=document, schema_ref=schema_ref, seen=seen):
        _merge_into(merged, part)
    return merged


def _parts(
    node: Mapping[str, Any],
    *,
    document: Mapping[str, Any],
    schema_ref: str,
    seen: frozenset[str],
) -> Iterator[Mapping[str, Any]]:
    """Yield the referenced shapes first, then the node's own keywords."""
    ref = node.get(REF_KEYWORD)
    if isinstance(ref, str) and ref not in seen:
        target = _resolve(ref, document=document, schema_ref=schema_ref)
        if target is not None:
            target_node, target_document, target_ref = target
            yield from _parts(
                target_node,
                document=target_document,
                schema_ref=target_ref,
                seen=seen | {ref},
            )

    for member in node.get(ALL_OF_KEYWORD, []) or []:
        if isinstance(member, Mapping):
            yield from _parts(member, document=document, schema_ref=schema_ref, seen=seen)

    yield {key: value for key, value in node.items() if key not in COMPOSITION_KEYWORDS}


def _resolve(
    ref: str,
    *,
    document: Mapping[str, Any],
    schema_ref: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any], str] | None:
    """Resolve one `$ref` to (node, its document, the ref that document came from)."""
    if ref.startswith(INTERNAL_REF_PREFIX):
        node: Any = document
        for segment in ref.lstrip("#/").split("/"):
            if not isinstance(node, Mapping) or segment not in node:
                return None
            node = node[segment]
        return (node, document, schema_ref) if isinstance(node, Mapping) else None

    target_ref = sibling_ref(schema_ref, ref)
    target_document = load_schema(target_ref)
    return target_document, target_document, target_ref


def _merge_into(merged: dict[str, Any], part: Mapping[str, Any]) -> None:
    """Merge one composition member. Later members win; `required` accumulates."""
    for key, value in part.items():
        if key == "properties" and isinstance(value, Mapping):
            existing = merged.setdefault("properties", {})
            for name, subschema in value.items():
                # A child re-declaring a property refines it rather than replacing it
                # (`artifact_type` narrows the base declaration to a const).
                if isinstance(existing.get(name), Mapping) and isinstance(subschema, Mapping):
                    existing[name] = {**existing[name], **subschema}
                else:
                    existing[name] = subschema
        elif key == "required" and isinstance(value, list):
            accumulated = merged.setdefault("required", [])
            accumulated.extend(item for item in value if item not in accumulated)
        else:
            merged[key] = value
