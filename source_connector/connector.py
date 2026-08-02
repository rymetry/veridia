"""Read one change (a commit range) out of the configured target repository.

This is the W1 input boundary (North Star §5.1). It returns the diff and the changed
files, plus the refs that say what the change *is* — those refs become the
`source_refs` a downstream artifact must carry, and the source grounding gate
(T-057) judges exactly that field.

Only a local git repository is read. No credentials are involved, so none can leak.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from change_impact_generator.diff_parser import ChangedFile, parse_unified_diff

from source_connector.errors import DiffParseError
from source_connector.git_repository import resolve_commit_sha, run_git
from source_connector.settings import TargetRepository

# --find-renames so a moved file is one rename rather than an add plus a delete.
# --no-color / --no-ext-diff so the output is the parser's input, not a human's.
DIFF_ARGS = ("diff", "--no-color", "--no-ext-diff", "--find-renames")
REF_SCHEME = "git"
RANGE_SEPARATOR = "..."


@dataclass(frozen=True)
class ChangeSet:
    """One change read from the target repository."""

    repository_label: str
    base_sha: str
    head_sha: str
    changed_files: tuple[ChangedFile, ...]
    diff_text: str
    source_refs: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "repository_label": self.repository_label,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "source_refs": list(self.source_refs),
            "changed_files": [
                {
                    "path": file.path,
                    "change_type": file.change_type,
                    "lines_added": file.lines_added,
                    "lines_deleted": file.lines_deleted,
                    "old_path": file.old_path,
                }
                for file in self.changed_files
            ],
            "diff_text": self.diff_text,
        }


@dataclass(frozen=True)
class SourceConnector:
    """Fetch changes from one configured target repository."""

    repository: TargetRepository

    def fetch_change(
        self,
        base: str,
        head: str,
        *,
        change_ref: str | None = None,
    ) -> ChangeSet:
        """Return the change between two revisions.

        `change_ref` is an optional durable reference the caller knows and the
        repository does not — a PR URL, an issue link. It is carried into
        `source_refs` ahead of the derived git ref because it survives longer.

        Raises:
            RepositoryNotFoundError: the configured repository is missing.
            RevisionRangeError: a revision is unusable or unresolvable.
            GitCommandError: git itself failed.
        """
        repo_path = self.repository.resolved_path()
        base_sha = resolve_commit_sha(repo_path, base)
        head_sha = resolve_commit_sha(repo_path, head)

        # Three-dot: what `head` added since it diverged from `base`, which is the
        # change under review rather than every difference between two branches.
        diff_text = run_git(repo_path, *DIFF_ARGS, f"{base_sha}{RANGE_SEPARATOR}{head_sha}")

        return ChangeSet(
            repository_label=self.repository.label,
            base_sha=base_sha,
            head_sha=head_sha,
            changed_files=_changed_files(diff_text, base_sha, head_sha),
            diff_text=diff_text,
            source_refs=self._source_refs(base_sha, head_sha, change_ref),
        )

    def run_git(self, *args: str) -> str:
        """Run one git command in the target repository (escape hatch for callers)."""
        return run_git(self.repository.resolved_path(), *args)

    def _source_refs(
        self,
        base_sha: str,
        head_sha: str,
        change_ref: str | None,
    ) -> tuple[str, ...]:
        derived = f"{REF_SCHEME}://{self.repository.label}/{base_sha}{RANGE_SEPARATOR}{head_sha}"
        if change_ref and change_ref.strip():
            return (change_ref.strip(), derived)
        return (derived,)


def _changed_files(diff_text: str, base_sha: str, head_sha: str) -> tuple[ChangedFile, ...]:
    """Parse the diff, treating "no output" as a real answer rather than an error.

    `parse_unified_diff` rejects a diff with no file entries, which is right for its
    own CLI (an empty input there is a mistake) but wrong here: a range where nothing
    changed is a legitimate result. Only genuinely empty git output is short-circuited
    — output that is non-empty yet unparsable stays an error, with context added.
    """
    if not diff_text.strip():
        return ()
    try:
        return parse_unified_diff(diff_text)
    except ValueError as exc:
        raise DiffParseError(
            f"could not parse the diff for {base_sha}{RANGE_SEPARATOR}{head_sha}: {exc}"
        ) from exc
