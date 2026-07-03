"""qa-skills registry metadata contract and consistency tests.

T-022:
- registry metadata mirrors North Star §28.2 "残すもの"
- registry.yaml validates against qa-skills/registry.schema.json
- registry entries stay consistent with their skill package manifests
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).parent.parent
QA_SKILLS_DIR = REPO_ROOT / "qa-skills"
REGISTRY_SCHEMA_PATH = QA_SKILLS_DIR / "registry.schema.json"
REGISTRY_PATH = QA_SKILLS_DIR / "registry.yaml"

SECTION_28_2_REGISTRY_FIELDS = frozenset(
    {
        "skill_id",
        "version",
        "owner",
        "allowed_tools",
        "input_schema",
        "output_schema",
        "schema_version",
        "eval_status",
        "last_successful_run",
        "policy_violation_count",
        "policy_violation_metrics",
        "changelog",
    }
)


def load_schema() -> dict[str, Any]:
    return json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))


def load_registry() -> dict[str, Any]:
    loaded = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema(), format_checker=FormatChecker())


class TestSkillRegistrySchemaItself:
    def test_schema_file_exists_outside_artifact_schemas_dir(self) -> None:
        assert REGISTRY_SCHEMA_PATH.is_file(), (
            f"registry schema正本が存在しない: {REGISTRY_SCHEMA_PATH}"
        )
        assert REGISTRY_SCHEMA_PATH.parent == QA_SKILLS_DIR

    def test_schema_is_valid_against_draft_2020_12_metaschema(self) -> None:
        Draft202012Validator.check_schema(load_schema())

    def test_schema_declares_draft_2020_12(self) -> None:
        assert load_schema()["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_section_28_2_fields_are_represented_by_entry_properties(self) -> None:
        entry_properties = set(load_schema()["properties"]["skills"]["items"]["properties"])
        missing = SECTION_28_2_REGISTRY_FIELDS - entry_properties
        assert not missing, f"§28.2 registry metadata未表現field: {missing}"


class TestSkillRegistry:
    def test_registry_yaml_passes_schema(self, validator: Draft202012Validator) -> None:
        validator.validate(load_registry())

    def test_template_skill_entry_is_registered(self) -> None:
        entries = load_registry()["skills"]
        assert {
            "skill_id": "template-skill",
            "version": "0.1.0",
            "owner": "qa-platform",
            "package_path": "_template",
        } in [
            {
                "skill_id": entry["skill_id"],
                "version": entry["version"],
                "owner": entry["owner"],
                "package_path": entry["package_path"],
            }
            for entry in entries
        ]

    @pytest.mark.parametrize("field", sorted(SECTION_28_2_REGISTRY_FIELDS | {"package_path"}))
    def test_missing_required_entry_field_fails(
        self, validator: Draft202012Validator, field: str
    ) -> None:
        entry = {k: v for k, v in load_registry()["skills"][0].items() if k != field}
        registry = {**load_registry(), "skills": [entry]}
        with pytest.raises(ValidationError):
            validator.validate(registry)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            ("skill_id", "TemplateSkill"),
            ("version", "1.0"),
            ("owner", ""),
            ("package_path", "../_template"),
            ("allowed_tools", "pytest"),
            ("input_schema", "/input.schema.json"),
            ("output_schema", ""),
            ("schema_version", "v1"),
            ("eval_status", "green"),
            ("last_successful_run", "2026-07-03 12:00:00"),
            ("policy_violation_count", -1),
            ("policy_violation_metrics", {"blocked": -1}),
            ("changelog", "../changelog.md"),
        ],
    )
    def test_type_or_value_violation_fails(
        self, validator: Draft202012Validator, field: str, invalid_value: Any
    ) -> None:
        entry = {**load_registry()["skills"][0], field: invalid_value}
        registry = {**load_registry(), "skills": [entry]}
        with pytest.raises(ValidationError):
            validator.validate(registry)


class TestSkillRegistryConsistency:
    def test_registry_entries_match_existing_skill_directories_and_manifest_versions(self) -> None:
        from skill_registry import validate_registry_consistency

        validate_registry_consistency(load_registry(), QA_SKILLS_DIR)

    def test_missing_skill_directory_is_detected(self) -> None:
        from skill_registry import SkillRegistryConsistencyError, validate_registry_consistency

        entry = {**load_registry()["skills"][0], "package_path": "missing-skill"}
        registry = {**load_registry(), "skills": [entry]}

        with pytest.raises(SkillRegistryConsistencyError, match="missing-skill"):
            validate_registry_consistency(registry, QA_SKILLS_DIR)

    def test_manifest_version_mismatch_is_detected(self) -> None:
        from skill_registry import SkillRegistryConsistencyError, validate_registry_consistency

        entry = {**load_registry()["skills"][0], "version": "9.9.9"}
        registry = {**load_registry(), "skills": [entry]}

        with pytest.raises(SkillRegistryConsistencyError, match="version mismatch"):
            validate_registry_consistency(registry, QA_SKILLS_DIR)
