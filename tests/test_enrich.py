"""Tests for enrichment (merging stubs + scraped HTML)."""

from fusion_lap.enrich import enrich_ir
from fusion_lap.ir import IR, ClassDef, MethodDef, PropertyDef


def test_enrich_adds_descriptions():
    ir = IR()
    ir.add_class(ClassDef(
        name="ExtrudeFeature",
        namespace="adsk.fusion",
        parent="Feature",
        methods={"deleteMe": MethodDef(name="deleteMe", returns="bool")},
        properties={"operation": PropertyDef(name="operation", type="FeatureOperations")},
    ))

    scraped = {
        "ExtrudeFeature": ClassDef(
            name="ExtrudeFeature",
            description="An extrude feature in a design.",
            methods={"deleteMe": MethodDef(name="deleteMe", description="Deletes this feature.")},
            properties={"operation": PropertyDef(name="operation", description="Gets the operation type.")},
        ),
    }

    enrich_ir(ir, scraped)

    cls = ir.namespaces["adsk.fusion"]["ExtrudeFeature"]
    assert cls.description == "An extrude feature in a design."
    assert cls.methods["deleteMe"].description == "Deletes this feature."
    assert cls.methods["deleteMe"].returns == "bool"
    assert cls.properties["operation"].description == "Gets the operation type."
    assert cls.properties["operation"].type == "FeatureOperations"


def test_enrich_adds_new_classes_from_html():
    ir = IR()
    scraped = {
        "NewClass": ClassDef(
            name="NewClass",
            description="Found in HTML but not stubs.",
            parent="Base",
        ),
    }

    enrich_ir(ir, scraped)

    all_names = [c.name for c in ir.all_classes()]
    assert "NewClass" in all_names
