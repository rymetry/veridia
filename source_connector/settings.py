"""Where the target repository lives, kept out of the code that reads it.

Phase 1's target is veridia itself (T-024), but nothing here names it. The whole point
of this module is that pointing at a different repository is a configuration change,
not a code change.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from source_connector.errors import RepositoryNotFoundError
from source_connector.trust import DEFAULT_TRUST_LEVEL, validate_trust_level

REPO_PATH_ENV = "VERIDIA_TARGET_REPO_PATH"
REPO_LABEL_ENV = "VERIDIA_TARGET_REPO_LABEL"
REPO_TRUST_ENV = "VERIDIA_TARGET_REPO_TRUST_LEVEL"
GIT_DIR_NAME = ".git"


@dataclass(frozen=True)
class TargetRepository:
    """A local git repository to read changes from, plus how it is labelled.

    `trust_level` is configuration, never something a downstream skill decides
    (ADR-0009 Decision 2). It defaults to trusted because pointing the configuration
    at a repository is the act of trusting it; anything else must say so explicitly.
    """

    path: Path
    label: str
    trust_level: str = DEFAULT_TRUST_LEVEL

    def __post_init__(self) -> None:
        validate_trust_level(self.trust_level)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> TargetRepository:
        """Build the target from the environment.

        Raises:
            RepositoryNotFoundError: the path variable is unset or blank.
            TrustLevelError: the configured trust level is not one the contract allows.
        """
        source = os.environ if env is None else env
        raw_path = source.get(REPO_PATH_ENV, "")
        if not raw_path.strip():
            raise RepositoryNotFoundError(
                f"{REPO_PATH_ENV} is not set: the target repository must be configured "
                "outside the code (T-026)"
            )
        path = Path(raw_path).expanduser().resolve()
        label = source.get(REPO_LABEL_ENV, "").strip() or path.name
        trust_level = source.get(REPO_TRUST_ENV, "").strip() or DEFAULT_TRUST_LEVEL
        return cls(path=path, label=label, trust_level=trust_level)

    def resolved_path(self) -> Path:
        """Return the repository root, checking it is really a git repository.

        Raises:
            RepositoryNotFoundError: the path is absent or holds no git repository.
        """
        path = self.path.expanduser().resolve()
        if not path.is_dir():
            raise RepositoryNotFoundError(f"target repository path does not exist: {path}")
        # A submodule checkout carries `.git` as a file, not a directory
        if not (path / GIT_DIR_NAME).exists():
            raise RepositoryNotFoundError(f"target repository path is not a git repository: {path}")
        return path
