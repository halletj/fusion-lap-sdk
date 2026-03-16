"""Tests for stub auto-discovery."""

import os
from unittest.mock import patch
from fusion_lap.discover import find_stubs, StubSource


def test_find_stubs_returns_stub_source():
    result = find_stubs()
    assert result is None or isinstance(result, StubSource)


def test_stub_source_has_path_and_kind():
    src = StubSource(path="/fake/path/adsk", kind="fusion_install")
    assert src.path == "/fake/path/adsk"
    assert src.kind == "fusion_install"


def test_find_stubs_respects_fusion_path_env(tmp_path):
    adsk_dir = tmp_path / "Api" / "Python" / "packages" / "adsk"
    adsk_dir.mkdir(parents=True)
    (adsk_dir / "__init__.pyi").write_text("# stub")

    with patch.dict(os.environ, {"FUSION_PATH": str(tmp_path)}):
        result = find_stubs()
    assert result is not None
    assert result.kind == "fusion_env"
