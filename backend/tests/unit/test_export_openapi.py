"""OpenAPI export script: deterministic output containing the known endpoints."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "export_openapi.py"


@pytest.fixture(scope="module")
def script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("export_openapi", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_contains_known_paths(script: ModuleType, tmp_path: Path) -> None:
    out = tmp_path / "nested" / "openapi.json"
    assert script.main(["export_openapi.py", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.endswith("}\n")
    document = json.loads(text)
    assert "/health/ready" in document["paths"]
    assert "/api/v1/config/public-flags" in document["paths"]


def test_export_is_identical_on_two_runs(script: ModuleType, tmp_path: Path) -> None:
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    script.main(["export_openapi.py", str(first)])
    script.main(["export_openapi.py", str(second)])
    assert first.read_bytes() == second.read_bytes()


def test_export_rejects_extra_arguments(script: ModuleType, tmp_path: Path) -> None:
    assert script.main(["export_openapi.py", str(tmp_path / "a"), "extra"]) == 2
