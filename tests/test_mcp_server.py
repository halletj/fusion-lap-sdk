"""Tests for MCP server tool functions."""

from pathlib import Path
from fusion_lap.mcp_server import lookup_domain, search_lap, get_graph


def test_lookup_domain(tmp_path):
    (tmp_path / "fusion-sketch.lap").write_text("[classes]\nSketch : Base\n  name: str\n")
    result = lookup_domain("sketch", str(tmp_path))
    assert "Sketch" in result


def test_lookup_domain_not_found(tmp_path):
    result = lookup_domain("nonexistent", str(tmp_path))
    assert "not found" in result.lower()


def test_search_lap(tmp_path):
    (tmp_path / "fusion-features.lap").write_text("[classes]\nExtrudeFeature : Feature\n  operation: FeatureOperations\n")
    (tmp_path / "fusion-sketch.lap").write_text("[classes]\nSketch : Base\n")
    results = search_lap("Extrude", str(tmp_path))
    assert "ExtrudeFeature" in results
    assert "fusion-features.lap" in results


def test_get_graph(tmp_path):
    (tmp_path / "fusion-graph.lap").write_text("[graph]\nApplication\n  .activeDocument -> Document\n")
    result = get_graph(str(tmp_path))
    assert "Application" in result
