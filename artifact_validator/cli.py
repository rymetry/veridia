"""Command line interface for artifact validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from artifact_validator import ArtifactValidationError, validate_artifact_file

EXIT_VALID = 0
EXIT_INVALID = 1
EXIT_INPUT_ERROR = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an artifact JSON file.")
    parser.add_argument("artifact_path", type=Path, help="Path to an artifact JSON file")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit validation errors as JSON instead of text",
    )
    args = parser.parse_args(argv)

    try:
        validate_artifact_file(args.artifact_path)
    except ArtifactValidationError as exc:
        _print_validation_error(args.artifact_path, exc, json_output=args.json)
        return EXIT_INVALID
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    print(f"valid: {args.artifact_path}")
    return EXIT_VALID


def _print_validation_error(
    artifact_path: Path,
    error: ArtifactValidationError,
    *,
    json_output: bool,
) -> None:
    if json_output:
        payload = {"path": str(artifact_path), **error.to_dict()}
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return

    print(f"invalid: {artifact_path}", file=sys.stderr)
    for issue in error.errors:
        print(
            f"- {issue.field_path}: {issue.message} "
            f"(validator={issue.validator}, schema_path={issue.schema_path})",
            file=sys.stderr,
        )


if __name__ == "__main__":
    raise SystemExit(main())
