"""Build ChangeImpactSpec candidate artifacts from unified diffs."""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import Any

from change_impact_generator.diff_parser import ChangedFile, parse_unified_diff

ARTIFACT_VERSION = "0.1.0"
ARTIFACT_TYPE = "change_impact_spec"
DEFAULT_GENERATED_AT = "1970-01-01T00:00:00Z"
DEFAULT_CONFIDENCE = 0.4
DEFAULT_SOURCE_REF = "diff://stdin"
HASH_LENGTH = 12
TRACE_HASH_LENGTH = 16
HIGH_RISK_ROOTS = frozenset({"policies", "schemas", "artifact_validator", "models"})
MEDIUM_RISK_ROOTS = frozenset({"src", "qa-skills", "test_asset_index_generator"})
LOW_RISK_ROOTS = frozenset({"docs", "tests"})


def generate_change_impact_spec(
    diff_text: str,
    *,
    source_ref: str = DEFAULT_SOURCE_REF,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Generate a deterministic candidate-level ChangeImpactSpec artifact."""
    timestamp = generated_at or DEFAULT_GENERATED_AT
    changed_files = parse_unified_diff(diff_text)
    fingerprint = _fingerprint(source_ref, timestamp, changed_files)

    return {
        "artifact_id": f"ART-CIS-{fingerprint}",
        "artifact_type": ARTIFACT_TYPE,
        "version": ARTIFACT_VERSION,
        "source_refs": [source_ref],
        "created_by": {
            "agent": "change-impact-generator",
            "skill": "change-impact-analysis",
            "model": "none",
        },
        "confidence": DEFAULT_CONFIDENCE,
        "status": "draft",
        "requires_human_review": True,
        "trace_id": _trace_id(timestamp, fingerprint),
        "created_at": timestamp,
        "change_impact_id": f"CIS-{fingerprint}",
        "changed_files": [_changed_file_to_dict(file) for file in changed_files],
        "changed_components": _changed_components(changed_files),
        "impacted_requirements": [],
        "impacted_risks": [],
        "impacted_apis": [],
    }


def _changed_file_to_dict(file: ChangedFile) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": file.path,
        "change_type": file.change_type,
        "risk_level": _risk_level_for_path(file.path),
        "component": _component_for_path(file.path),
        "lines_added": file.lines_added,
        "lines_deleted": file.lines_deleted,
        "analysis_status": "candidate_path_only_phase_0",
    }
    if file.old_path is not None:
        payload["old_path"] = file.old_path
    return payload


def _changed_components(changed_files: tuple[ChangedFile, ...]) -> list[str]:
    components = {_component_for_path(file.path) for file in changed_files}
    return sorted(components)


def _component_for_path(path: str) -> str:
    parts = PurePosixPath(path).parts
    if not parts:
        raise ValueError(f"failed to derive component from path: {path}")
    if parts[0] == "src" and len(parts) >= 2:
        return parts[1]
    if parts[0] == "qa-skills" and len(parts) >= 2:
        return f"qa-skills/{parts[1]}"
    return parts[0]


def _risk_level_for_path(path: str) -> str:
    root = PurePosixPath(path).parts[0]
    if root in HIGH_RISK_ROOTS:
        return "high"
    if root in MEDIUM_RISK_ROOTS:
        return "medium"
    if root in LOW_RISK_ROOTS:
        return "low"
    return "medium"


def _fingerprint(source_ref: str, generated_at: str, changed_files: tuple[ChangedFile, ...]) -> str:
    parts: list[str] = [source_ref, generated_at]
    for file in changed_files:
        parts.extend(
            [
                file.path,
                file.change_type,
                str(file.lines_added),
                str(file.lines_deleted),
                file.old_path or "",
            ]
        )
    return _stable_hash("\n".join(parts))


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:HASH_LENGTH].upper()


def _trace_id(generated_at: str, fingerprint: str) -> str:
    date_part = _trace_date_part(generated_at)
    stable_hex = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:TRACE_HASH_LENGTH]
    return f"trace-{date_part}-{stable_hex}"


def _trace_date_part(generated_at: str) -> str:
    date_text = generated_at[:10]
    compact = date_text.replace("-", "")
    if len(compact) != 8 or not compact.isdigit():
        raise ValueError(f"generated_at must start with YYYY-MM-DD: {generated_at!r}")
    return compact
