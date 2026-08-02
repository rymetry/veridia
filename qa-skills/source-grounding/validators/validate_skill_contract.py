"""Template helpers for checking the required skill package file set."""

from __future__ import annotations

REQUIRED_PACKAGE_PATHS = (
    "SKILL.md",
    "manifest.yaml",
    "input.schema.json",
    "output.schema.json",
    "preconditions.md",
    "postconditions.md",
    "failure_modes.md",
    "evals/positive_prompts.csv",
    "evals/negative_prompts.csv",
    "evals/regression_cases.yaml",
    "validators/validate_schema.py",
    "validators/validate_skill_contract.py",
    "scripts/run_skill.py",
    "changelog.md",
)


def required_package_paths() -> tuple[str, ...]:
    return REQUIRED_PACKAGE_PATHS
