"""Command line interface for reading one change out of the target repository."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from source_connector.connector import ChangeSet, SourceConnector
from source_connector.errors import SourceConnectorError
from source_connector.settings import (
    REPO_LABEL_ENV,
    REPO_PATH_ENV,
    REPO_TRUST_ENV,
    TargetRepository,
)
from source_connector.trust import DEFAULT_TRUST_LEVEL

EXIT_OK = 0
EXIT_INPUT_ERROR = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read a commit range from the target repository as a ChangeSet JSON."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help=f"Target repository path; defaults to ${REPO_PATH_ENV}",
    )
    parser.add_argument(
        "--label",
        default=None,
        help=f"Name used in derived refs; defaults to ${REPO_LABEL_ENV} or the directory name",
    )
    parser.add_argument(
        "--trust-level",
        default=None,
        help=(
            f"Trust label for this source; defaults to ${REPO_TRUST_ENV} or "
            f"{DEFAULT_TRUST_LEVEL}. Set by configuration, never by a skill (ADR-0009)"
        ),
    )
    parser.add_argument("--base", required=True, help="Base revision of the change")
    parser.add_argument("--head", required=True, help="Head revision of the change")
    parser.add_argument(
        "--change-ref",
        default=None,
        help="Durable reference for the change (for example a PR URL), added to source_refs",
    )
    parser.add_argument("--output", type=Path, required=True, help="ChangeSet JSON output path")
    args = parser.parse_args(argv)

    try:
        repository = _repository(args.repo, args.label, args.trust_level)
        change = SourceConnector(repository=repository).fetch_change(
            args.base, args.head, change_ref=args.change_ref
        )
        _write_json(args.output, change)
    except SourceConnectorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except OSError as exc:
        print(f"error: failed to write {args.output}: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    print(f"read {len(change.changed_files)} changed file(s): {args.output}")
    return EXIT_OK


def _repository(
    repo: Path | None,
    label: str | None,
    trust_level: str | None,
) -> TargetRepository:
    """Build the target, letting explicit flags override the configured values."""
    if repo is None:
        configured = TargetRepository.from_env()
        return TargetRepository(
            path=configured.path,
            label=label or configured.label,
            trust_level=trust_level or configured.trust_level,
        )
    resolved = repo.expanduser().resolve()
    return TargetRepository(
        path=resolved,
        label=label or resolved.name,
        trust_level=trust_level or DEFAULT_TRUST_LEVEL,
    )


def _write_json(output_path: Path, change: ChangeSet) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(change.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
