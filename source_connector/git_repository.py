"""Run git against the target repository with a fixed argv and no shell.

Revisions come from callers and end up as git arguments, so they are checked before
use: a value starting with `-` would be read by git as an option rather than a
revision, which changes what the command does.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from source_connector.errors import GitCommandError, RevisionRangeError

GIT_TIMEOUT_SECONDS = 30
OPTION_PREFIX = "-"


def run_git(repo_path: Path, *args: str) -> str:
    """Run one git command in `repo_path` and return stdout verbatim.

    Raises:
        GitCommandError: git could not be run, timed out, or exited non-zero.
    """
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitCommandError(
            f"git {args[0] if args else ''} failed in {repo_path}: {exc}"
        ) from exc
    if completed.returncode != 0:
        raise GitCommandError(
            f"git {args[0] if args else ''} failed in {repo_path} "
            f"(exit {completed.returncode}): {completed.stderr.strip()}"
        )
    return completed.stdout


def validate_revision(revision: str) -> str:
    """Reject revisions git would not read as revisions.

    Raises:
        RevisionRangeError: the revision is blank or would be parsed as an option.
    """
    if not revision or not revision.strip():
        raise RevisionRangeError("revision must not be empty")
    if revision.startswith(OPTION_PREFIX):
        raise RevisionRangeError(
            f"revision must not start with {OPTION_PREFIX!r} (git would read it as an "
            f"option): {revision!r}"
        )
    return revision


def resolve_commit_sha(repo_path: Path, revision: str) -> str:
    """Resolve a revision to a full commit SHA so the range is reproducible later.

    Raises:
        RevisionRangeError: the revision is unusable or does not name a commit.
    """
    validate_revision(revision)
    try:
        output = run_git(
            repo_path, "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}"
        )
    except GitCommandError as exc:
        raise RevisionRangeError(
            f"cannot resolve revision {revision!r} in {repo_path}: {exc}"
        ) from exc
    return output.strip()
