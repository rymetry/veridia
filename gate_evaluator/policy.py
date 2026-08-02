"""Load `policies/gate-policy.yaml` as the stage lookup used by the evaluator.

The policy file is the source of truth for which stage each gate runs at (§17.0).
It is validated against its own schema on every load: a config that does not satisfy
its contract must not silently decide what blocks a release.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from gate_evaluator.errors import GatePolicyError

POLICIES_DIR = Path(__file__).resolve().parent.parent / "policies"
DEFAULT_POLICY_PATH = POLICIES_DIR / "gate-policy.yaml"
POLICY_SCHEMA_PATH = POLICIES_DIR / "gate-policy.schema.json"

POLICY_VERSION_FIELD = "policy_version"
GATES_FIELD = "gates"
STAGE_FIELD = "stage"


@dataclass(frozen=True)
class GatePolicy:
    """Which stage each gate runs at, plus the policy version that says so."""

    policy_version: str
    stages: Mapping[str, str]

    @classmethod
    def load(cls, path: str | Path = DEFAULT_POLICY_PATH) -> GatePolicy:
        """Read and validate one GatePolicy config.

        Raises:
            GatePolicyError: the file is unreadable, unparsable, or breaks its schema.
        """
        policy_path = Path(path)
        document = _read_document(policy_path)
        _validate(document, policy_path)
        gates: dict[str, Any] = document[GATES_FIELD]
        return cls(
            policy_version=document[POLICY_VERSION_FIELD],
            stages=MappingProxyType(
                {gate_id: gate[STAGE_FIELD] for gate_id, gate in gates.items()}
            ),
        )


def _read_document(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GatePolicyError(f"failed to read the gate policy {path}: {exc}") from exc
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise GatePolicyError(f"failed to parse the gate policy {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise GatePolicyError(f"the gate policy must be a mapping: {path}")
    return document


def _validate(document: Mapping[str, Any], path: Path) -> None:
    try:
        schema = json.loads(POLICY_SCHEMA_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise GatePolicyError(f"failed to read {POLICY_SCHEMA_PATH}: {exc}") from exc
    try:
        Draft202012Validator(schema).validate(document)
    except ValidationError as exc:
        raise GatePolicyError(
            f"{path.name} does not satisfy the gate-policy schema at "
            f"{'.'.join(str(part) for part in exc.absolute_path) or '$'}: {exc.message}"
        ) from exc
