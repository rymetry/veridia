"""Source Connector: read changes out of the target repository (North Star §5.1).

    TargetRepository.from_env() → SourceConnector.fetch_change(base, head) → ChangeSet

This is the W1 input boundary. Two properties are load-bearing:

- **the target is configuration, not code.** Phase 1's target is veridia itself
  (T-024) but nothing in this module names it; pointing elsewhere is an env change
- **veridia handles no credentials.** Only a local git repository is read, so there
  is nothing to leak here (the same principle as ADR-0005, which delegates
  authentication to a CLI veridia never passes credentials to)
"""

from source_connector.connector import ChangeSet, SourceConnector
from source_connector.errors import (
    DiffParseError,
    GitCommandError,
    RepositoryNotFoundError,
    RevisionRangeError,
    SourceConnectorError,
    TrustLevelError,
)
from source_connector.settings import (
    REPO_LABEL_ENV,
    REPO_PATH_ENV,
    REPO_TRUST_ENV,
    TargetRepository,
)
from source_connector.trust import DEFAULT_TRUST_LEVEL, trust_levels

TRUST_LEVELS = trust_levels()

__all__ = [
    "DEFAULT_TRUST_LEVEL",
    "REPO_LABEL_ENV",
    "REPO_PATH_ENV",
    "REPO_TRUST_ENV",
    "TRUST_LEVELS",
    "ChangeSet",
    "DiffParseError",
    "GitCommandError",
    "RepositoryNotFoundError",
    "RevisionRangeError",
    "SourceConnector",
    "SourceConnectorError",
    "TargetRepository",
    "TrustLevelError",
    "trust_levels",
]
