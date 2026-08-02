"""Load veridia's own skill packages from `qa-skills/`.

The layout differs from sqk-core's: metadata lives in `manifest.yaml` (validated
against `qa-skills/manifest.schema.json`) rather than in SKILL.md frontmatter, so
`SKILL.md` here is instruction text end to end.

The manifest names its outputs by artifact title (`SourceMap`). Those are resolved to
the `veridia://` schema_refs the handoff envelope declares (ADR-0010), so a manifest
that names a contract nobody defines fails at load rather than at model output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from artifact_validator.schema_ref import veridia_ref_for_title
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from skill_runner.errors import SkillNotFoundError, SkillSourceError
from skill_runner.skill_source import NAME_RE, SKILL_FILENAME, SkillDefinition

QA_SKILLS_DIR = Path(__file__).resolve().parent.parent / "qa-skills"
MANIFEST_FILENAME = "manifest.yaml"
MANIFEST_SCHEMA_FILENAME = "manifest.schema.json"
# The scaffold to copy, never something to execute. It is excluded by `NAME_RE`: a
# skill name cannot start with `_`. That is the single mechanism — an extra explicit
# check was tried and removed because mutation testing showed nothing could reach it.
# `test_scaffold_name_cannot_be_a_skill_name` pins the assumption it rests on.
TEMPLATE_DIR_NAME = "_template"


@dataclass(frozen=True)
class QaSkillSource:
    """Read veridia skill packages from `qa-skills/`."""

    root: Path = QA_SKILLS_DIR

    def available(self) -> tuple[str, ...]:
        """Return every loadable skill name, sorted. The template is not one."""
        if not self.root.is_dir():
            return ()
        return tuple(
            sorted(
                path.parent.name
                for path in self.root.glob(f"*/{MANIFEST_FILENAME}")
                if NAME_RE.match(path.parent.name) and (path.parent / SKILL_FILENAME).is_file()
            )
        )

    def load(self, name: str) -> SkillDefinition:
        """Load one veridia skill package by name.

        Raises:
            SkillNotFoundError: unknown name.
            SkillSourceError: the manifest is unreadable or breaks its contract.
            SqkSchemaError: a declared output names no veridia contract.
        """
        package = self._package_for(name)
        manifest = self._manifest(package)
        if manifest["name"] != name:
            raise SkillSourceError(
                f"manifest name {manifest['name']!r} does not match its directory {name!r}: "
                f"{package / MANIFEST_FILENAME}"
            )

        return SkillDefinition(
            name=manifest["name"],
            version=manifest["version"],
            description=manifest["description"].strip(),
            body=(package / SKILL_FILENAME).read_text(encoding="utf-8"),
            output_schema_refs=tuple(
                sorted(veridia_ref_for_title(title) for title in manifest["outputs"]["required"])
            ),
        )

    def _package_for(self, name: str) -> Path:
        available = self.available()
        if name not in available:
            raise SkillNotFoundError(
                f"unknown qa-skill {name!r}; available: {', '.join(available) or '(none)'}"
            )
        return self.root / name

    def _manifest(self, package: Path) -> dict[str, Any]:
        path = package / MANIFEST_FILENAME
        try:
            manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise SkillSourceError(f"failed to read {path}: {exc}") from exc
        except yaml.YAMLError as exc:
            raise SkillSourceError(f"failed to parse {path}: {exc}") from exc
        if not isinstance(manifest, dict):
            raise SkillSourceError(f"skill manifest must be a mapping: {path}")

        # The package contract is checked at load, not only in CI: a runtime that
        # executes an invalid package produces output nobody can interpret.
        try:
            Draft202012Validator(self._manifest_schema()).validate(manifest)
        except ValidationError as exc:
            raise SkillSourceError(
                f"{path} does not satisfy the skill manifest contract at "
                f"{'.'.join(str(part) for part in exc.absolute_path) or '$'}: {exc.message}"
            ) from exc
        return manifest

    def _manifest_schema(self) -> dict[str, Any]:
        path = self.root / MANIFEST_SCHEMA_FILENAME
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise SkillSourceError(f"failed to read {path}: {exc}") from exc
