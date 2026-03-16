"""Tests for the full build pipeline."""

from pathlib import Path
from fusion_lap.build import build_lap_files

FIXTURES = Path(__file__).parent / "fixtures" / "fake_adsk"


def test_build_produces_lap_files(tmp_path):
    build_lap_files(
        output_dir=str(tmp_path),
        stubs_path=str(FIXTURES),
        no_enrich=True,
    )
    assert (tmp_path / "fusion-base.lap").exists()
    assert (tmp_path / "fusion-graph.lap").exists()
    assert (tmp_path / "fusion-gotchas.lap").exists()


def test_build_base_contains_graph(tmp_path):
    build_lap_files(
        output_dir=str(tmp_path),
        stubs_path=str(FIXTURES),
        no_enrich=True,
    )
    base = (tmp_path / "fusion-base.lap").read_text()
    assert "[graph]" in base
    assert "[gotchas]" in base


def test_build_domain_files_contain_classes(tmp_path):
    build_lap_files(
        output_dir=str(tmp_path),
        stubs_path=str(FIXTURES),
        no_enrich=True,
    )
    features_file = tmp_path / "fusion-features.lap"
    if features_file.exists():
        content = features_file.read_text()
        assert "ExtrudeFeature" in content
