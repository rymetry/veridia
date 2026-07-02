"""scripts/gen_models.py(schemas/ → Pydanticモデル生成とdiff検証)のテスト。

ADR-0002: 正本はJSON Schema、Pydanticモデルは単方向生成の生成物。
生成物はコミットし、CIで再生成→diff無しを検証する(T-002からの申し送り)。
"""

from __future__ import annotations

import importlib
import json
import shutil
from pathlib import Path

import pytest

import gen_models
from gen_models import (
    ModelGenerationError,
    collect_schema_files,
    find_drift,
    generate_all,
    module_name_for,
)

REPO_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
MODELS_DIR = REPO_ROOT / "models"


class TestModuleNameFor:
    def test_maps_schema_filename_to_python_module(self) -> None:
        assert module_name_for("artifact-base.schema.json") == "artifact_base.py"

    def test_rejects_filename_without_schema_suffix(self) -> None:
        with pytest.raises(ValueError, match="schema.json"):
            module_name_for("artifact-base.json")


class TestCollectSchemaFiles:
    def test_finds_schema_files_in_repo(self) -> None:
        names = [p.name for p in collect_schema_files(SCHEMAS_DIR)]
        assert "artifact-base.schema.json" in names

    def test_ignores_non_schema_files(self) -> None:
        # schemas/README.md は収集対象外
        assert all(p.name.endswith(".schema.json") for p in collect_schema_files(SCHEMAS_DIR))

    def test_missing_dir_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            collect_schema_files(tmp_path / "no-such-dir")


@pytest.fixture(scope="module")
def fresh_gen_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """repoのschemas/から一時ディレクトリへ1回だけ生成した結果(module内で共有)。"""
    out_dir = tmp_path_factory.mktemp("fresh_models")
    generate_all(SCHEMAS_DIR, out_dir)
    return out_dir


class TestGenerateAll:
    def test_writes_model_module_per_schema(self, fresh_gen_dir: Path) -> None:
        assert (fresh_gen_dir / "artifact_base.py").is_file()

    def test_generated_module_defines_model_class(self, fresh_gen_dir: Path) -> None:
        text = (fresh_gen_dir / "artifact_base.py").read_text(encoding="utf-8")
        assert "class ArtifactBase" in text

    def test_generated_module_has_do_not_edit_header(self, fresh_gen_dir: Path) -> None:
        first_line = (
            (fresh_gen_dir / "artifact_base.py").read_text(encoding="utf-8").splitlines()[0]
        )
        assert first_line.startswith("#")
        assert "do not edit" in first_line or "編集しない" in first_line

    def test_generation_is_deterministic(self, fresh_gen_dir: Path, tmp_path: Path) -> None:
        # CI diff検証の前提: 同一入力から同一バイト列が生成される
        generate_all(SCHEMAS_DIR, tmp_path)
        for fresh in sorted(tmp_path.glob("*.py")):
            assert fresh.read_bytes() == (fresh_gen_dir / fresh.name).read_bytes()

    def test_broken_schema_raises_with_context(self, tmp_path: Path) -> None:
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        (schemas / "broken.schema.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(ModelGenerationError, match="broken.schema.json"):
            generate_all(schemas, tmp_path / "out")

    def test_colliding_module_names_fail_fast(self, tmp_path: Path) -> None:
        # a-b と a_b は同じ a_b.py に写る。黙った後勝ち上書きは片方の契約を消すためfail-fastする
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        minimal = json.dumps(
            {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}
        )
        (schemas / "a-b.schema.json").write_text(minimal, encoding="utf-8")
        (schemas / "a_b.schema.json").write_text(minimal, encoding="utf-8")
        with pytest.raises(ValueError, match="a_b.py"):
            generate_all(schemas, tmp_path / "out")


class TestFindDrift:
    def test_no_drift_for_fresh_generation(self, fresh_gen_dir: Path) -> None:
        assert find_drift(SCHEMAS_DIR, fresh_gen_dir) == ()

    def test_detects_stale_model(self, fresh_gen_dir: Path, tmp_path: Path) -> None:
        tampered = tmp_path / "models"
        shutil.copytree(fresh_gen_dir, tampered)
        target = tampered / "artifact_base.py"
        target.write_text(target.read_text(encoding="utf-8") + "\n# 手編集\n", encoding="utf-8")
        drifts = find_drift(SCHEMAS_DIR, tampered)
        assert any("artifact_base.py" in d and "stale" in d for d in drifts)

    def test_detects_missing_model(self, fresh_gen_dir: Path, tmp_path: Path) -> None:
        empty_models = tmp_path / "models"
        empty_models.mkdir()
        drifts = find_drift(SCHEMAS_DIR, empty_models)
        assert any("artifact_base.py" in d and "missing" in d for d in drifts)

    def test_detects_orphan_model(self, fresh_gen_dir: Path, tmp_path: Path) -> None:
        with_orphan = tmp_path / "models"
        shutil.copytree(fresh_gen_dir, with_orphan)
        (with_orphan / "ghost.py").write_text("# 対応するschemaが無い\n", encoding="utf-8")
        drifts = find_drift(SCHEMAS_DIR, with_orphan)
        assert any("ghost.py" in d and "orphan" in d for d in drifts)


class TestCommittedModels:
    def test_committed_models_match_schemas(self) -> None:
        # コミット済み生成物が正本(schemas/)と乖離していないこと(ADR-0002の乖離防止)
        assert find_drift(SCHEMAS_DIR, MODELS_DIR) == ()


def load_schema_example() -> dict:
    """schema正本に埋め込まれた examples[0] を有効サンプルとして使う。"""
    schema = json.loads((SCHEMAS_DIR / "artifact-base.schema.json").read_text(encoding="utf-8"))
    return schema["examples"][0]


class TestGeneratedPydanticModel:
    def test_generated_model_accepts_valid_sample(self) -> None:
        artifact_base = importlib.import_module("models.artifact_base")
        model = artifact_base.ArtifactBase(**load_schema_example())
        assert model.artifact_id == "REQ-001"

    def test_generated_model_rejects_empty_source_refs(self) -> None:
        artifact_base = importlib.import_module("models.artifact_base")
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            artifact_base.ArtifactBase(**{**load_schema_example(), "source_refs": []})

    def test_source_refs_items_are_plain_strings(self) -> None:
        # schema契約上 source_refs は string の配列。生成モデルがRootModel等でラップすると
        # 比較・in判定・startswith等の値のセマンティクスが静かに壊れる(code review指摘)
        artifact_base = importlib.import_module("models.artifact_base")
        example = load_schema_example()
        model = artifact_base.ArtifactBase(**example)
        assert all(isinstance(ref, str) for ref in model.source_refs)
        assert list(model.source_refs) == example["source_refs"]

    def test_created_at_without_timezone_is_rejected(self) -> None:
        # 契約意図はRFC 3339 date-time(timezone必須)。生成モデルはAwareDatetimeで強制する。
        # 生JSON側はdraft 2020-12のformat=注釈のため通る(test_artifact_base_schema.py参照)。
        # この非対称はschema descriptionに記録済みで、生JSON側の強制はT-008で決める
        artifact_base = importlib.import_module("models.artifact_base")
        from pydantic import ValidationError

        naive = {**load_schema_example(), "created_at": "2026-07-02T10:00:00"}
        with pytest.raises(ValidationError):
            artifact_base.ArtifactBase(**naive)


class TestCli:
    """main() のexit-code契約(0=一致 / 1=乖離 / 2=入力異常)。CIはこの終了コードに依存する。"""

    @pytest.fixture
    def repo_like_root(self, fresh_gen_dir: Path, tmp_path: Path) -> Path:
        """schemas+生成済みmodelsを持つ一時リポジトリルート(再生成コストを避けfixtureから複製)。"""
        root = tmp_path / "root"
        (root / "schemas").mkdir(parents=True)
        shutil.copy(
            SCHEMAS_DIR / "artifact-base.schema.json",
            root / "schemas" / "artifact-base.schema.json",
        )
        shutil.copytree(fresh_gen_dir, root / "models")
        return root

    def test_check_exits_0_when_models_match(
        self, repo_like_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(gen_models, "_REPO_ROOT", repo_like_root)
        assert gen_models.main(["--check"]) == 0

    def test_check_exits_1_on_drift(
        self, repo_like_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = repo_like_root / "models" / "artifact_base.py"
        target.write_text(target.read_text(encoding="utf-8") + "\n# 手編集\n", encoding="utf-8")
        monkeypatch.setattr(gen_models, "_REPO_ROOT", repo_like_root)
        assert gen_models.main(["--check"]) == 1

    def test_exits_2_when_schemas_dir_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(gen_models, "_REPO_ROOT", tmp_path / "empty-root")
        assert gen_models.main(["--check"]) == 2

    def test_generate_mode_exits_0_and_writes(
        self, repo_like_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        shutil.rmtree(repo_like_root / "models")
        monkeypatch.setattr(gen_models, "_REPO_ROOT", repo_like_root)
        assert gen_models.main([]) == 0
        assert (repo_like_root / "models" / "artifact_base.py").is_file()
