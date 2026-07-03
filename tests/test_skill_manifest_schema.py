"""qa-skills manifest schema and template package contract tests.

T-021:
- template package mirrors North Star §7.1 structure
- template manifest passes the manifest schema
- missing required fields and type violations fail
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).parent.parent
QA_SKILLS_DIR = REPO_ROOT / "qa-skills"
SCHEMA_PATH = QA_SKILLS_DIR / "manifest.schema.json"
TEMPLATE_DIR = QA_SKILLS_DIR / "_template"
TEMPLATE_MANIFEST_PATH = TEMPLATE_DIR / "manifest.yaml"

REQUIRED_MANIFEST_FIELDS = frozenset(
    {
        "name",
        "version",
        "owner",
        "description",
        "inputs",
        "outputs",
    }
)

SECTION_7_1_TEMPLATE_PATHS = (
    "SKILL.md",
    "manifest.yaml",
    "input.schema.json",
    "output.schema.json",
    "preconditions.md",
    "postconditions.md",
    "failure_modes.md",
    "examples",
    "evals/positive_prompts.csv",
    "evals/negative_prompts.csv",
    "evals/regression_cases.yaml",
    "validators/validate_schema.py",
    "validators/validate_skill_contract.py",
    "scripts/run_skill.py",
    "changelog.md",
)


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_template_manifest() -> dict[str, Any]:
    loaded = yaml.safe_load(TEMPLATE_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema())


class TestSkillManifestSchemaItself:
    def test_schema_file_exists_outside_artifact_schemas_dir(self) -> None:
        assert SCHEMA_PATH.is_file(), f"manifest schema正本が存在しない: {SCHEMA_PATH}"
        assert SCHEMA_PATH.parent == QA_SKILLS_DIR

    def test_schema_is_valid_against_draft_2020_12_metaschema(self) -> None:
        Draft202012Validator.check_schema(load_schema())

    def test_schema_declares_draft_2020_12(self) -> None:
        assert load_schema()["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_required_fields_are_phase_0_author_and_t_022_registry_dependencies(self) -> None:
        schema = load_schema()
        assert set(schema["required"]) == REQUIRED_MANIFEST_FIELDS

    def test_all_required_fields_have_property_definitions(self) -> None:
        schema = load_schema()
        missing = REQUIRED_MANIFEST_FIELDS - set(schema["properties"])
        assert not missing, f"required だが properties 未定義のfield: {missing}"


class TestTemplatePackage:
    @pytest.mark.parametrize("relative_path", SECTION_7_1_TEMPLATE_PATHS)
    def test_template_contains_section_7_1_package_structure(self, relative_path: str) -> None:
        path = TEMPLATE_DIR / relative_path
        assert path.exists(), f"§7.1 template構成要素が存在しない: {path}"

    def test_template_manifest_passes_schema(self, validator: Draft202012Validator) -> None:
        validator.validate(load_template_manifest())


class TestInvalidManifests:
    @pytest.mark.parametrize("field", sorted(REQUIRED_MANIFEST_FIELDS))
    def test_missing_required_field_fails(
        self, validator: Draft202012Validator, field: str
    ) -> None:
        manifest = {k: v for k, v in load_template_manifest().items() if k != field}
        with pytest.raises(ValidationError):
            validator.validate(manifest)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            ("name", "TemplateSkill"),
            ("version", "1.0"),
            ("owner", ""),
            ("description", ""),
            ("inputs", {"required": "RequirementSpec"}),
            ("outputs", {"required": []}),
            ("validators", ["validate_schema.py"]),
        ],
    )
    def test_type_or_value_violation_fails(
        self, validator: Draft202012Validator, field: str, invalid_value: Any
    ) -> None:
        manifest = {**load_template_manifest(), field: invalid_value}
        with pytest.raises(ValidationError):
            validator.validate(manifest)
