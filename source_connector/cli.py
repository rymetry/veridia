"""Command line interface for reading one change out of the target repository."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from source_connector.connector import ChangeSet, SourceConnector
from source_connector.errors import SourceConnectorError
from source_connector.settings import REPO_LABEL_ENV, REPO_PATH_ENV, TargetRepository

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
        repository = _repository(args.repo, args.label)
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


def _repository(repo: Path | None, label: str | None) -> TargetRepository:
    if repo is None:
        configured = TargetRepository.from_env()
        return configured if label is None else TargetRepository(configured.path, label)
    resolved = repo.expanduser().resolve()
    return TargetRepository(path=resolved, label=label or resolved.name)


def _write_json(output_path: Path, change: ChangeSet) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(change.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
