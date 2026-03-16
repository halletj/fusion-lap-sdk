"""Tests for the intermediate representation module."""

from fusion_lap.ir import IR, ClassDef, MethodDef, PropertyDef, EnumDef


def test_create_empty_ir():
    ir = IR()
    assert ir.namespaces == {}


def test_add_class():
    ir = IR()
    cls = ClassDef(
        name="Point3D",
        namespace="adsk.core",
        parent="Base",
        description="A 3D point.",
        properties={
            "x": PropertyDef(name="x", type="float", description="The x coordinate."),
        },
        methods={
            "create": MethodDef(
                name="create",
                args=[("x", "float"), ("y", "float"), ("z", "float")],
                returns="Point3D",
                static=True,
                description="Creates a Point3D.",
            ),
        },
    )
    ir.add_class(cls)
    assert "adsk.core" in ir.namespaces
    assert "Point3D" in ir.namespaces["adsk.core"]
    assert ir.namespaces["adsk.core"]["Point3D"].parent == "Base"


def test_add_enum():
    ir = IR()
    enum = EnumDef(
        name="FeatureOperations",
        namespace="adsk.fusion",
        values=["JoinFeatureOperation", "CutFeatureOperation", "IntersectFeatureOperation", "NewBodyFeatureOperation"],
    )
    ir.add_enum(enum)
    assert "FeatureOperations" in ir.enums["adsk.fusion"]


def test_merge_enriches_existing_class():
    ir = IR()
    cls = ClassDef(name="Point3D", namespace="adsk.core", parent="Base")
    ir.add_class(cls)

    enrichment = ClassDef(
        name="Point3D",
        namespace="adsk.core",
        description="A 3D point used for coordinates.",
        properties={
            "x": PropertyDef(name="x", type="float", description="The x coordinate."),
        },
    )
    ir.merge_class(enrichment)

    merged = ir.namespaces["adsk.core"]["Point3D"]
    assert merged.description == "A 3D point used for coordinates."
    assert "x" in merged.properties
    assert merged.parent == "Base"  # preserved from original


def test_all_classes():
    ir = IR()
    ir.add_class(ClassDef(name="Point3D", namespace="adsk.core", parent="Base"))
    ir.add_class(ClassDef(name="Sketch", namespace="adsk.fusion", parent="Base"))
    all_classes = ir.all_classes()
    names = [c.name for c in all_classes]
    assert "Point3D" in names
    assert "Sketch" in names
