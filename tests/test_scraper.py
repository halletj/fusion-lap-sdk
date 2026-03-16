"""Tests for HTML scraper."""

from pathlib import Path
from fusion_lap.scraper import parse_class_page
from fusion_lap.ir import ClassDef

FIXTURES = Path(__file__).parent / "fixtures" / "html"


def test_parse_class_page():
    html = (FIXTURES / "ExtrudeFeature.htm").read_text()
    cls = parse_class_page("ExtrudeFeature", html)
    assert isinstance(cls, ClassDef)
    assert cls.name == "ExtrudeFeature"
    assert cls.parent == "Feature"
    assert cls.description == "An extrude feature in a design."


def test_parse_class_page_methods():
    html = (FIXTURES / "ExtrudeFeature.htm").read_text()
    cls = parse_class_page("ExtrudeFeature", html)
    assert "deleteMe" in cls.methods
    assert cls.methods["deleteMe"].description == "Deletes this feature."


def test_parse_class_page_properties():
    html = (FIXTURES / "ExtrudeFeature.htm").read_text()
    cls = parse_class_page("ExtrudeFeature", html)
    assert "operation" in cls.properties
    assert "profile" in cls.properties
