"""Tests for stub parser."""

from pathlib import Path
from fusion_lap.stubs import parse_stubs
from fusion_lap.ir import IR

FIXTURES = Path(__file__).parent / "fixtures" / "fake_adsk"


def test_parse_stubs_returns_ir():
    ir = parse_stubs(str(FIXTURES))
    assert isinstance(ir, IR)


def test_parse_finds_classes():
    ir = parse_stubs(str(FIXTURES))
    all_names = [c.name for c in ir.all_classes()]
    assert "Base" in all_names
    assert "Point3D" in all_names
    assert "Feature" in all_names
    assert "ExtrudeFeature" in all_names


def test_parse_inheritance():
    ir = parse_stubs(str(FIXTURES))
    point3d = ir.namespaces["adsk.core"]["Point3D"]
    assert point3d.parent == "Base"
    extrude = ir.namespaces["adsk.fusion"]["ExtrudeFeature"]
    assert extrude.parent == "Feature"


def test_parse_properties():
    ir = parse_stubs(str(FIXTURES))
    point3d = ir.namespaces["adsk.core"]["Point3D"]
    assert "x" in point3d.properties
    assert point3d.properties["x"].type == "float"


def test_parse_methods():
    ir = parse_stubs(str(FIXTURES))
    extrude = ir.namespaces["adsk.fusion"]["ExtrudeFeature"]
    assert "setOneSideExtent" in extrude.methods
    method = extrude.methods["setOneSideExtent"]
    assert method.returns == "bool"
    assert len(method.args) == 2


def test_parse_static_methods():
    ir = parse_stubs(str(FIXTURES))
    point3d = ir.namespaces["adsk.core"]["Point3D"]
    assert "create" in point3d.methods
    assert point3d.methods["create"].static is True


def test_parse_enums():
    ir = parse_stubs(str(FIXTURES))
    all_enums = ir.all_enums()
    enum_names = [e.name for e in all_enums]
    assert "FeatureOperations" in enum_names
    ops = ir.enums["adsk.fusion"]["FeatureOperations"]
    assert "JoinFeatureOperation" in ops.values


def test_parse_detects_collections():
    ir = parse_stubs(str(FIXTURES))
    coll = ir.namespaces["adsk.fusion"]["ExtrudeFeatures"]
    assert coll.is_collection is True
