"""Command line interface for ChangeImpactSpec candidate generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from artifact_validator import ArtifactValidationError, validate_artifact

from change_impact_generator.generator import DEFAULT_SOURCE_REF, generate_change_impact_spec

EXIT_OK = 0
EXIT_VALIDATION_ERROR = 1
EXIT_INPUT_ERROR = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a candidate-level ChangeImpactSpec artifact JSON."
    )
    parser.add_argument("diff_path", type=Path, help="Unified git diff input path")
    parser.add_argument("output_path", type=Path, help="Artifact JSON output path")
    parser.add_argument(
        "--source-ref",
        default=DEFAULT_SOURCE_REF,
        help="Source reference recorded in source_refs; defaults to diff://stdin",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="RFC 3339 timestamp for created_at; defaults to deterministic sentinel",
    )
    args = parser.parse_args(argv)

    try:
        artifact = generate_change_impact_spec(
            args.diff_path.read_text(encoding="utf-8"),
            source_ref=args.source_ref,
            generated_at=args.generated_at,
        )
        validate_artifact(artifact)
        _write_json(args.output_path, artifact)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except ArtifactValidationError as exc:
        print(f"invalid generated artifact: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR

    print(f"generated: {args.output_path}")
    return EXIT_OK


def _write_json(output_path: Path, artifact: dict[str, object]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
