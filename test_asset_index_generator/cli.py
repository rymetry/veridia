"""Command line interface for TestAssetIndex generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from artifact_validator import ArtifactValidationError, validate_artifact

from test_asset_index_generator.generator import generate_test_asset_index

EXIT_OK = 0
EXIT_VALIDATION_ERROR = 1
EXIT_INPUT_ERROR = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a TestAssetIndex artifact JSON.")
    parser.add_argument("repository_path", type=Path, help="Repository root to scan")
    parser.add_argument("output_path", type=Path, help="Artifact JSON output path")
    parser.add_argument(
        "--repository",
        help="Repository name to record in scope; defaults to repository_path.name",
    )
    parser.add_argument(
        "--branch",
        default="unknown",
        help="Branch name to record in scope; defaults to 'unknown'",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="RFC 3339 timestamp for created_at/indexed_at; defaults to deterministic sentinel",
    )
    args = parser.parse_args(argv)

    try:
        artifact = generate_test_asset_index(
            args.repository_path,
            repository_name=args.repository,
            branch=args.branch,
            generated_at=args.generated_at,
        )
        validate_artifact(artifact)
        _write_json(args.output_path, artifact)
    except ArtifactValidationError as exc:
        print(f"invalid generated artifact: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    print(f"generated: {args.output_path}")
    return EXIT_OK


def _write_json(output_path: Path, artifact: dict[str, object]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
