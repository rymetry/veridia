"""GatePolicy versioned config contract tests.

T-023:
- policies/gate-policy.yaml validates against policies/gate-policy.schema.json
- every North Star §17.1 gate has a stage and threshold definition
- only the §17.0 initial four gates start in block stage
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).parent.parent
POLICIES_DIR = REPO_ROOT / "policies"
GATE_POLICY_SCHEMA_PATH = POLICIES_DIR / "gate-policy.schema.json"
GATE_POLICY_PATH = POLICIES_DIR / "gate-policy.yaml"

SECTION_17_1_GATE_IDS = frozenset(
    {
        "source_grounding",
        "oracle",
        "testability",
        "evidence",
        "security",
        "human_review",
        "flaky",
        "judge_calibration",
        "regression",
        "cost",
        "change_impact",
        "test_impact",
        "coverage_gap",
        "reuse_dedup",
        "performance_risk",
        "reporting",
    }
)

INITIAL_BLOCK_GATE_IDS = frozenset(
    {
        "source_grounding",
        "oracle",
        "evidence",
        "security",
    }
)


def load_schema() -> dict[str, Any]:
    assert GATE_POLICY_SCHEMA_PATH.is_file(), (
        f"GatePolicy schema正本が存在しない: {GATE_POLICY_SCHEMA_PATH}"
    )
    return json.loads(GATE_POLICY_SCHEMA_PATH.read_text(encoding="utf-8"))


def load_policy() -> dict[str, Any]:
    assert GATE_POLICY_PATH.is_file(), f"GatePolicy正本が存在しない: {GATE_POLICY_PATH}"
    loaded = yaml.safe_load(GATE_POLICY_PATH.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema())


class TestGatePolicySchemaItself:
    def test_schema_file_exists_outside_artifact_schemas_dir(self) -> None:
        assert GATE_POLICY_SCHEMA_PATH.is_file(), (
            f"GatePolicy schema正本が存在しない: {GATE_POLICY_SCHEMA_PATH}"
        )
        assert GATE_POLICY_SCHEMA_PATH.parent == POLICIES_DIR

    def test_schema_is_valid_against_draft_2020_12_metaschema(self) -> None:
        Draft202012Validator.check_schema(load_schema())

    def test_schema_declares_draft_2020_12(self) -> None:
        assert load_schema()["$schema"] == "https://json-schema.org/draft/2020-12/schema"


class TestGatePolicy:
    def test_gate_policy_yaml_passes_schema(self, validator: Draft202012Validator) -> None:
        validator.validate(load_policy())

    def test_policy_declares_version_and_north_star_section_17_0_ref(self) -> None:
        policy = load_policy()

        assert policy["policy_version"] == "0.1.0"
        assert "§17.0" in policy["north_star_refs"]
        assert "較正前の出発点" in policy["calibration_note"]

    def test_policy_defines_every_section_17_1_gate_once(self) -> None:
        policy_gate_ids = set(load_policy()["gates"])

        assert policy_gate_ids == SECTION_17_1_GATE_IDS

    def test_each_section_17_1_gate_has_stage_and_thresholds(self) -> None:
        for gate_id, gate in load_policy()["gates"].items():
            assert gate["stage"] in {"shadow", "warn", "block"}, gate_id
            assert gate["thresholds"], gate_id

    def test_only_initial_four_gates_start_in_block_stage(self) -> None:
        block_gate_ids = {
            gate_id for gate_id, gate in load_policy()["gates"].items() if gate["stage"] == "block"
        }

        assert block_gate_ids == INITIAL_BLOCK_GATE_IDS

    def test_non_initial_block_gates_start_in_shadow_or_warn(self) -> None:
        non_initial_gate_ids = SECTION_17_1_GATE_IDS - INITIAL_BLOCK_GATE_IDS
        policy = load_policy()

        for gate_id in sorted(non_initial_gate_ids):
            assert policy["gates"][gate_id]["stage"] in {"shadow", "warn"}, gate_id

    @pytest.mark.parametrize(
        ("path", "invalid_value"),
        [
            (("gates", "source_grounding", "stage"), "enforce"),
            (("gates", "flaky", "thresholds", 0, "value"), ["95%"]),
            (("gates", "security", "thresholds", 0, "operator"), "under"),
        ],
    )
    def test_type_or_value_violation_fails(
        self,
        validator: Draft202012Validator,
        path: tuple[str | int, ...],
        invalid_value: Any,
    ) -> None:
        policy = copy.deepcopy(load_policy())
        target: Any = policy
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = invalid_value

        with pytest.raises(ValidationError):
            validator.validate(policy)

    @pytest.mark.parametrize(
        "missing_path",
        [
            ("policy_version",),
            ("gates", "oracle"),
            ("gates", "evidence", "stage"),
            ("gates", "security", "thresholds"),
            ("gates", "reporting", "thresholds", 0, "value"),
        ],
    )
    def test_missing_required_field_fails(
        self,
        validator: Draft202012Validator,
        missing_path: tuple[str | int, ...],
    ) -> None:
        policy = copy.deepcopy(load_policy())
        target: Any = policy
        for key in missing_path[:-1]:
            target = target[key]
        del target[missing_path[-1]]

        with pytest.raises(ValidationError):
            validator.validate(policy)
