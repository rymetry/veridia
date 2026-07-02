"""Pytest asset discovery for TestAssetIndex generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PYTEST_FILE_PREFIX = "test_"
PYTEST_FILE_SUFFIX = "_test.py"
TESTS_DIR_NAME = "tests"
IGNORED_DIR_NAMES = frozenset({"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"})


@dataclass(frozen=True, slots=True)
class TestAsset:
    """One discovered test asset."""

    path: str
    test_type: str


def discover_pytest_assets(repository_path: Path) -> tuple[TestAsset, ...]:
    """Discover pytest files under a repository's tests directory."""
    repo_root = repository_path.resolve()
    if not repo_root.is_dir():
        raise ValueError(f"repository path is not a directory: {repository_path}")

    tests_dir = repo_root / TESTS_DIR_NAME
    if not tests_dir.exists():
        return ()

    paths = sorted(
        _relative_posix_path(path, repo_root)
        for path in tests_dir.rglob("*.py")
        if _is_pytest_file(path) and not _has_ignored_parent(path, tests_dir)
    )
    return tuple(TestAsset(path=path, test_type="unit") for path in paths)


def _is_pytest_file(path: Path) -> bool:
    name = path.name
    return name.startswith(PYTEST_FILE_PREFIX) or name.endswith(PYTEST_FILE_SUFFIX)


def _has_ignored_parent(path: Path, tests_dir: Path) -> bool:
    relative_parts = path.relative_to(tests_dir).parts
    return any(part.startswith(".") or part in IGNORED_DIR_NAMES for part in relative_parts[:-1])


def _relative_posix_path(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()
