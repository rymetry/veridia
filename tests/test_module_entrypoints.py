"""Module entrypoint import-safety tests."""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "sandbox_env.__main__",
        "artifact_validator.__main__",
        "test_asset_index_generator.__main__",
    ],
)
def test_main_modules_do_not_execute_on_import(module_name: str) -> None:
    importlib.import_module(module_name)
