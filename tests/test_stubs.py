"""Tests for stub parser."""

from pathlib import Path
import pytest
from fusion_lap.stubs import parse_stubs
from fusion_lap.ir import IR

FIXTURES = Path(__file__).parent / "fixtures" / "fake_adsk"

REAL_STUBS = "/Users/halletj/Library/Application Support/Autodesk/webdeploy/production/d33deb94f63c0f9e07daa3f1ea6a07e40d838e5e/Autodesk Fusion.app/Contents/Api/Python/packages/adsk"


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


# --- Integration tests for real SWIG stubs ---


def test_parse_real_stubs():
    """Parse real Fusion SWIG stubs and verify key classes are found."""
    if not Path(REAL_STUBS).exists():
        pytest.skip("Real Fusion stubs not available")

    ir = parse_stubs(REAL_STUBS)
    all_names = [c.name for c in ir.all_classes()]

    # Should find hundreds of classes
    assert len(all_names) > 500

    # Key classes should be present
    assert "Application" in all_names
    assert "Point3D" in all_names
    assert "Sketch" in all_names
    assert "ExtrudeFeature" in all_names
    assert "Component" in all_names

    # SWIG infrastructure should be filtered out
    assert "_SwigNonDynamicMeta" not in all_names
    assert "SwigPyIterator" not in all_names

    # Point3D should have properties (from module-level assignments)
    point3d = ir.namespaces["adsk.core"]["Point3D"]
    assert "x" in point3d.properties
    assert "y" in point3d.properties
    assert "z" in point3d.properties
    assert point3d.properties["x"].type == "float"

    # Point3D should have methods with descriptions
    assert "create" in point3d.methods
    assert point3d.methods["create"].static is True
    assert point3d.methods["create"].returns in ("Point3D", "adsk.core.Point3D")

    # Should find enums
    all_enums = [e.name for e in ir.all_enums()]
    assert "FeatureOperations" in all_enums


def test_parse_real_stubs_inheritance():
    """Verify inheritance is correctly parsed from real stubs."""
    if not Path(REAL_STUBS).exists():
        pytest.skip("Real Fusion stubs not available")

    ir = parse_stubs(REAL_STUBS)

    point3d = ir.namespaces["adsk.core"]["Point3D"]
    assert point3d.parent == "Base"

    extrude = ir.namespaces["adsk.fusion"]["ExtrudeFeature"]
    assert extrude.parent == "Feature"
