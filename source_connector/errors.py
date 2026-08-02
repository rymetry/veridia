"""Source Connector error types."""

from __future__ import annotations


class SourceConnectorError(RuntimeError):
    """Base class for every source acquisition failure."""


class RepositoryNotFoundError(SourceConnectorError):
    """Raised when the configured target repository is missing or is not a git repo."""


class RevisionRangeError(SourceConnectorError):
    """Raised when a revision is unusable or cannot be resolved in the target repo.

    Distinct from `GitCommandError`: the caller named something git cannot accept,
    rather than git itself failing. An unresolvable revision must never degrade to an
    empty diff — that would look like "nothing changed".
    """


class GitCommandError(SourceConnectorError):
    """Raised when a git invocation fails. Carries git's own stderr."""


class DiffParseError(SourceConnectorError):
    """Raised when git produced output the diff parser could not read.

    An empty range is not this: no changes is a legitimate result and yields no files.
    This means output arrived and did not look like a unified diff.
    """
