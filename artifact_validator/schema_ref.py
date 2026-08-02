"""Route a handoff envelope's `schema_ref` to the contract family that owns it.

Two families ride the same envelope (ADR-0010):

    schemas/<file>.schema.json            → sqk-core  (upstream's own convention)
    veridia://schemas/<file>.schema.json  → veridia   (ADR-0009)

There is deliberately **no fallback between them**. Trying sqk-core and then veridia
would work today only because no filename appears in both; the first collision would
silently validate against whichever family happened to be tried first. An unroutable
ref is an error.
"""

from __future__ import annotations

from pathlib import Path

from jsonschema import Draft202012Validator

from artifact_validator.errors import SqkSchemaError
from artifact_validator.schema_store import (
    load_schema as load_veridia_schema,
)
from artifact_validator.schema_store import (
    schema_filenames,
    validator_for_schema_file,
)
from artifact_validator.sqk_schema_store import (
    available_schema_refs as sqk_schema_refs,
)
from artifact_validator.sqk_schema_store import (
    load_schema as load_sqk_schema,
)
from artifact_validator.sqk_schema_store import (
    validator_for_schema_ref as sqk_validator_for_schema_ref,
)

VERIDIA_SCHEME = "veridia://"
VERIDIA_REF_PREFIX = f"{VERIDIA_SCHEME}schemas/"

FAMILY_VERIDIA = "veridia"
FAMILY_SQK_CORE = "sqk-core"


def family_of(schema_ref: str) -> str:
    """Which contract family a `schema_ref` names, by namespace alone."""
    return FAMILY_VERIDIA if schema_ref.startswith(VERIDIA_SCHEME) else FAMILY_SQK_CORE


def declares_sqk_core_contract(envelope_artifacts: object) -> bool:
    """True when any envelope artifact declares a sqk-core `schema_ref`.

    Used to decide whether a RunRecord must carry `sqk_core.commit` (ADR-0010
    Decision 3). Malformed input answers False rather than raising: the envelope's own
    contract check is what reports its shape problems.
    """
    if not isinstance(envelope_artifacts, list):
        return False
    return any(
        isinstance(artifact, dict)
        and isinstance(artifact.get("schema_ref"), str)
        and family_of(artifact["schema_ref"]) == FAMILY_SQK_CORE
        for artifact in envelope_artifacts
    )


def available_schema_refs() -> tuple[str, ...]:
    """Every routable `schema_ref` across both families, sorted within each."""
    return sqk_schema_refs() + veridia_schema_refs()


def veridia_schema_refs() -> tuple[str, ...]:
    """Every veridia `schema_ref`, sorted."""
    return tuple(f"{VERIDIA_REF_PREFIX}{name}" for name in schema_filenames())


def validator_for_schema_ref(schema_ref: str) -> Draft202012Validator:
    """Return the validator for one `schema_ref`, whichever family owns it.

    Raises:
        SqkSchemaError: the ref names no schema in its family.
    """
    if family_of(schema_ref) == FAMILY_SQK_CORE:
        return sqk_validator_for_schema_ref(schema_ref)
    return validator_for_schema_file(_veridia_filename(schema_ref))


def load_schema(schema_ref: str) -> dict:
    """Read and parse the schema a `schema_ref` names, whichever family owns it."""
    if family_of(schema_ref) == FAMILY_SQK_CORE:
        return load_sqk_schema(schema_ref)
    return load_veridia_schema(_veridia_filename(schema_ref))


def _veridia_filename(schema_ref: str) -> str:
    """Map a veridia `schema_ref` to a filename directly under `schemas/`.

    The allowlist below is also the traversal defence: `schema_filenames()` holds bare
    `Path.name` values, so anything carrying a separator or `..` cannot match it. A
    separate parent-directory check was tried and removed — it was unreachable, which
    mutation testing showed by surviving its own deletion.
    """
    if not schema_ref.startswith(VERIDIA_REF_PREFIX):
        raise SqkSchemaError(
            f"veridia schema_ref must start with {VERIDIA_REF_PREFIX!r}: {schema_ref!r}"
        )
    filename = schema_ref[len(VERIDIA_REF_PREFIX) :]
    if filename not in schema_filenames():
        supported = ", ".join(veridia_schema_refs())
        raise SqkSchemaError(f"unknown schema_ref {schema_ref!r}; supported: {supported}")
    return filename


def sibling_ref(schema_ref: str, target: str) -> str:
    """Resolve a relative `$ref` filename against the referring schema's own ref.

    Both families name schemas by path, so replacing the last segment keeps the ref in
    the family it came from — routing never crosses families by accident.
    """
    head, separator, _ = schema_ref.rpartition("/")
    return f"{head}{separator}{target}" if separator else target


def veridia_ref_for(schema_path: str | Path) -> str:
    """Build the `schema_ref` a veridia schema file is named by."""
    return f"{VERIDIA_REF_PREFIX}{Path(schema_path).name}"


def veridia_ref_for_title(title: str) -> str:
    """Find the veridia `schema_ref` whose schema declares `title`.

    Skill manifests name their outputs by artifact title (`SourceMap`), not by file.
    Matching on the declared title rather than transforming the string means a manifest
    that names a contract nobody defines fails loudly instead of resolving to a
    plausible-looking filename.

    Raises:
        SqkSchemaError: no veridia schema declares that title.
    """
    for filename in schema_filenames():
        if load_veridia_schema(filename).get("title") == title:
            return f"{VERIDIA_REF_PREFIX}{filename}"
    raise SqkSchemaError(
        f"no veridia schema declares title {title!r}; known: {', '.join(sorted(_known_titles()))}"
    )


def _known_titles() -> set[str]:
    return {
        str(load_veridia_schema(name).get("title"))
        for name in schema_filenames()
        if load_veridia_schema(name).get("title")
    }
