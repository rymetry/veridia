"""Load sqk-core SKILL.md definitions for runtime use.

veridia reads SKILL.md explicitly rather than relying on Claude Code's skill
discovery: ADR-0005 Decision 5 requires running with cwd outside the repository and
with skill loading disabled, which makes the `.claude/skills` symlink unreachable by
design. Reading the file ourselves also puts the exact instruction text into the
trace and ties it to a pinned commit (ADR-0005 追記 2026-08-02).

`.claude/skills` stays the development-agent lane only (sqk-core-integration.md §3).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from skill_runner.errors import SkillNotFoundError, SkillSourceError

SQK_SKILLS_DIR = Path(__file__).resolve().parent.parent / "vendor" / "sqk-core" / "skills"
SKILL_FILENAME = "SKILL.md"
FRONTMATTER_RE = re.compile(r"\A---\n(?P<frontmatter>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)
NAME_RE = re.compile(r"\A[a-z0-9]+(-[a-z0-9]+)*\Z")


@dataclass(frozen=True)
class SkillDefinition:
    """One sqk-core skill: its declared contract plus the instruction body."""

    name: str
    version: str
    description: str
    body: str
    output_schema_refs: tuple[str, ...]

    @property
    def instruction_text(self) -> str:
        """The text handed to the model as the instruction half of the prompt."""
        return self.body.strip()


@dataclass(frozen=True)
class SqkSkillSource:
    """Read skills from the pinned sqk-core submodule."""

    root: Path = SQK_SKILLS_DIR

    def available(self) -> tuple[str, ...]:
        """Return every loadable skill name, sorted. Empty when the submodule is absent."""
        if not self.root.is_dir():
            return ()
        return tuple(
            sorted(
                path.parent.name
                for path in self.root.glob(f"*/{SKILL_FILENAME}")
                if NAME_RE.match(path.parent.name)
            )
        )

    def load(self, name: str) -> SkillDefinition:
        """Load one skill by name.

        Raises:
            SkillNotFoundError: unknown name, or the submodule is not checked out.
            SkillSourceError: the SKILL.md frontmatter is missing or malformed.
        """
        path = self._path_for(name)
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if match is None:
            raise SkillSourceError(f"SKILL.md has no YAML frontmatter: {path}")

        try:
            frontmatter = yaml.safe_load(match.group("frontmatter"))
        except yaml.YAMLError as exc:
            raise SkillSourceError(
                f"failed to parse SKILL.md frontmatter for {name}: {exc}"
            ) from exc
        if not isinstance(frontmatter, dict):
            raise SkillSourceError(f"SKILL.md frontmatter must be a mapping: {path}")

        return SkillDefinition(
            name=_required_str(frontmatter, "name", path),
            version=_required_str(frontmatter, "version", path),
            description=str(frontmatter.get("description", "")).strip(),
            body=match.group("body"),
            output_schema_refs=_output_schema_refs(frontmatter),
        )

    def _path_for(self, name: str) -> Path:
        available = self.available()
        if not available:
            raise SkillNotFoundError(
                f"no sqk-core skill found under {self.root}. the submodule is not checked out: "
                "run `git submodule update --init --recursive`"
            )
        if name not in available:
            raise SkillNotFoundError(f"unknown skill {name!r}; available: {', '.join(available)}")
        return self.root / name / SKILL_FILENAME


def _required_str(frontmatter: dict, key: str, path: Path) -> str:
    value = frontmatter.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SkillSourceError(f"SKILL.md frontmatter {key!r} must be a non-empty string: {path}")
    return value.strip()


def _output_schema_refs(frontmatter: dict) -> tuple[str, ...]:
    """Collect the `schema_ref`-style paths the skill declares under `outputs`.

    sqk-core writes them relative to the skill directory (`../../schemas/x.schema.json`);
    normalise to the repo-relative form the handoff envelope uses (`schemas/x.schema.json`).
    """
    outputs = frontmatter.get("outputs")
    if not isinstance(outputs, dict):
        return ()
    refs = []
    for entry in outputs.values():
        if isinstance(entry, dict) and isinstance(entry.get("schema"), str):
            refs.append(_normalise_ref(entry["schema"]))
    return tuple(sorted(set(refs)))


def _normalise_ref(schema_path: str) -> str:
    marker = "schemas/"
    index = schema_path.rfind(marker)
    return schema_path[index:] if index >= 0 else schema_path
