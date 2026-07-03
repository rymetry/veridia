"""Build TestAssetIndex artifacts from discovered test assets."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from test_asset_index_generator.discovery import TestAsset, discover_pytest_assets

ARTIFACT_VERSION = "0.1.0"
ARTIFACT_TYPE = "test_asset_index"
DEFAULT_GENERATED_AT = "1970-01-01T00:00:00Z"
DEFAULT_BRANCH = "unknown"
DEFAULT_CONFIDENCE = 0.6
HASH_LENGTH = 12
TRACE_HASH_LENGTH = 16


def generate_test_asset_index(
    repository_path: str | Path,
    *,
    repository_name: str | None = None,
    branch: str = DEFAULT_BRANCH,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Generate a deterministic TestAssetIndex artifact for pytest files."""
    repo_path = Path(repository_path)
    repo_name = repository_name or _repository_name(repo_path)
    timestamp = generated_at or DEFAULT_GENERATED_AT
    assets = discover_pytest_assets(repo_path)
    fingerprint = _fingerprint(repo_name, branch, timestamp, assets)

    return {
        "artifact_id": f"ART-TAI-{fingerprint}",
        "artifact_type": ARTIFACT_TYPE,
        "version": ARTIFACT_VERSION,
        "source_refs": [f"repo://{repo_name}/tests"],
        "created_by": {
            "agent": "test-asset-index-generator",
            "skill": "existing-test-discovery",
            "model": "none",
        },
        "confidence": DEFAULT_CONFIDENCE,
        "status": "draft",
        "requires_human_review": True,
        "trace_id": _trace_id(timestamp, fingerprint),
        "created_at": timestamp,
        "index_id": f"TAI-{fingerprint}",
        "indexed_at": timestamp,
        "scope": {
            "repository": repo_name,
            "branch": branch,
            "test_framework": "pytest",
            "test_root": "tests",
        },
        "assets": [_asset_to_dict(asset) for asset in assets],
    }


def _asset_to_dict(asset: TestAsset) -> dict[str, Any]:
    return {
        "test_id": f"TEST-PYTEST-{_stable_hash(asset.path)}",
        "test_type": asset.test_type,
        "path": asset.path,
        "covered_requirements": [],
        "covered_risks": [],
        "oracle_refs": [],
        "stability": {
            "flake_rate": None,
            "last_failed_at": None,
            "last_passed_at": None,
            "collection_status": "uncollected_phase_0",
        },
        "collection_status": {
            "coverage_mapping": "uncollected_phase_0",
            "stability_history": "uncollected_phase_0",
        },
    }


def _repository_name(repository_path: Path) -> str:
    name = repository_path.resolve().name
    if not name:
        raise ValueError(f"failed to derive repository name from path: {repository_path}")
    return name


def _fingerprint(
    repository_name: str, branch: str, generated_at: str, assets: tuple[TestAsset, ...]
) -> str:
    parts = [repository_name, branch, generated_at, *(asset.path for asset in assets)]
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
