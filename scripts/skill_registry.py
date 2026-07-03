"""Skill registry consistency helpers.

The registry schema validates metadata shape. These helpers check repository
state that JSON Schema cannot see, such as package directory existence and
manifest version agreement.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml


class SkillRegistryConsistencyError(ValueError):
    """Raised when registry metadata does not match skill package files."""


def validate_registry_consistency(registry: Mapping[str, Any], qa_skills_dir: Path) -> None:
    """Validate that registry entries point to existing packages and versions.

    Args:
        registry: Parsed registry document.
        qa_skills_dir: Repository-local `qa-skills/` directory.

    Raises:
        SkillRegistryConsistencyError: If any entry points outside qa-skills,
            lacks a package manifest, or disagrees with manifest version.
    """
    entries = registry.get("skills")
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        raise SkillRegistryConsistencyError("registry skills must be a sequence")

    issues: list[str] = []
    qa_skills_root = qa_skills_dir.resolve()
    seen_skill_ids: set[str] = set()

    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            issues.append(f"skills[{index}] must be a mapping")
            continue

        skill_id = _string_field(entry, "skill_id", index, issues)
        version = _string_field(entry, "version", index, issues)
        package_path = _string_field(entry, "package_path", index, issues)
        input_schema = _string_field(entry, "input_schema", index, issues)
        output_schema = _string_field(entry, "output_schema", index, issues)
        changelog = _string_field(entry, "changelog", index, issues)
        if not skill_id or not version or not package_path:
            continue
        if skill_id in seen_skill_ids:
            issues.append(f"{skill_id}: duplicate skill_id in registry")
            continue
        seen_skill_ids.add(skill_id)

        skill_dir = (qa_skills_root / package_path).resolve()
        if not _is_relative_to(skill_dir, qa_skills_root):
            issues.append(f"{skill_id}: package_path escapes qa-skills: {package_path}")
            continue
        if not skill_dir.is_dir():
            issues.append(f"{skill_id}: skill directory does not exist: {package_path}")
            continue

        manifest_path = skill_dir / "manifest.yaml"
        if not manifest_path.is_file():
            issues.append(f"{skill_id}: manifest.yaml does not exist in {package_path}")
            continue

        manifest = _load_manifest(manifest_path, skill_id, issues)
        if manifest is None:
            continue

        manifest_name = manifest.get("name")
        if manifest_name != skill_id:
            issues.append(
                f"{skill_id}: name mismatch: registry skill_id != manifest {manifest_name}"
            )
        manifest_version = manifest.get("version")
        if manifest_version != version:
            issues.append(
                f"{skill_id}: version mismatch: registry {version} != manifest {manifest_version}"
            )
        for field_name, relative_path in (
            ("input_schema", input_schema),
            ("output_schema", output_schema),
            ("changelog", changelog),
        ):
            if relative_path:
                _check_package_file(skill_id, field_name, relative_path, skill_dir, issues)

    if issues:
        raise SkillRegistryConsistencyError("; ".join(issues))


def _string_field(
    entry: Mapping[str, Any], field: str, index: int, issues: list[str]
) -> str | None:
    value = entry.get(field)
    if not isinstance(value, str) or not value:
        issues.append(f"skills[{index}].{field} must be a non-empty string")
        return None
    return value


def _load_manifest(
    manifest_path: Path, skill_id: str, issues: list[str]
) -> Mapping[str, Any] | None:
    try:
        loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        issues.append(f"{skill_id}: manifest.yaml is invalid YAML: {exc}")
        return None

    if not isinstance(loaded, Mapping):
        issues.append(f"{skill_id}: manifest.yaml must parse to a mapping")
        return None
    return loaded


def _check_package_file(
    skill_id: str,
    field_name: str,
    relative_path: str,
    skill_dir: Path,
    issues: list[str],
) -> None:
    path = (skill_dir / relative_path).resolve()
    if not _is_relative_to(path, skill_dir):
        issues.append(f"{skill_id}: {field_name} escapes package: {relative_path}")
        return
    if not path.is_file():
        issues.append(f"{skill_id}: {field_name} file does not exist: {relative_path}")


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True
