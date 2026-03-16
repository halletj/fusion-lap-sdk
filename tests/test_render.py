"""Tests for LAP renderer."""

from fusion_lap.ir import IR, ClassDef, MethodDef, PropertyDef, EnumDef
from fusion_lap.render import render_domain, render_graph, render_gotchas


def _make_test_ir():
    ir = IR()
    ir.add_class(ClassDef(
        name="Application",
        namespace="adsk.core",
        parent="Base",
        description="The top-level application object.",
        properties={
            "activeDocument": PropertyDef(name="activeDocument", type="Document", description="The active document."),
        },
    ))
    ir.add_class(ClassDef(
        name="ExtrudeFeature",
        namespace="adsk.fusion",
        parent="Feature",
        description="An extrude feature.",
        properties={
            "operation": PropertyDef(name="operation", type="FeatureOperations"),
        },
        methods={
            "deleteMe": MethodDef(name="deleteMe", returns="bool", description="Deletes this feature."),
            "setOneSideExtent": MethodDef(
                name="setOneSideExtent",
                args=[("extent", "ExtentDefinition"), ("direction", "ExtentDirections")],
                returns="bool",
            ),
        },
    ))
    ir.add_class(ClassDef(
        name="ExtrudeFeatures",
        namespace="adsk.fusion",
        is_collection=True,
        collection_item_type="ExtrudeFeature",
        methods={
            "item": MethodDef(name="item", args=[("index", "int")], returns="ExtrudeFeature"),
            "addSimple": MethodDef(
                name="addSimple",
                args=[("profile", "Profile"), ("distance", "ValueInput"), ("operation", "FeatureOperations")],
                returns="ExtrudeFeature",
            ),
        },
        properties={
            "count": PropertyDef(name="count", type="int"),
        },
    ))
    ir.add_enum(EnumDef(
        name="FeatureOperations",
        namespace="adsk.fusion",
        values=["JoinFeatureOperation", "CutFeatureOperation"],
    ))
    ir.gotchas = ["Units are centimeters internally"]
    return ir


def test_render_domain_contains_classes():
    ir = _make_test_ir()
    output = render_domain(ir, "features", ["*Feature", "*Features"])
    assert "ExtrudeFeature : Feature" in output
    assert "operation: FeatureOperations" in output
    assert "deleteMe() -> bool" in output
    assert "setOneSideExtent(" in output


def test_render_domain_contains_enums():
    ir = _make_test_ir()
    output = render_domain(ir, "features", ["*Feature", "*Features", "FeatureOperations"])
    assert "FeatureOperations:" in output
    assert "JoinFeatureOperation" in output


def test_render_collection_shorthand():
    ir = _make_test_ir()
    output = render_domain(ir, "features", ["*Feature", "*Features"])
    assert "*collection<ExtrudeFeature>" in output


def test_render_graph():
    ir = _make_test_ir()
    output = render_graph(ir)
    assert "[graph]" in output
    assert "Application" in output


def test_render_gotchas():
    ir = _make_test_ir()
    output = render_gotchas(ir)
    assert "[gotchas]" in output
    assert "centimeters" in output
