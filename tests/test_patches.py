"""Tests for the patches module."""

import tempfile
from pathlib import Path

import yaml

from fusion_lap.ir import IR, ClassDef, MethodDef, PropertyDef
from fusion_lap.patches import apply_patches


def _make_ir_with_class(name="TestClass", namespace="adsk.fusion", **kwargs):
    ir = IR()
    cls = ClassDef(name=name, namespace=namespace, **kwargs)
    ir.add_class(cls)
    return ir


def _write_patches(patches: dict) -> Path:
    path = Path(tempfile.mktemp(suffix=".yaml"))
    path.write_text(yaml.dump(patches))
    return path


def test_add_gotchas():
    ir = IR()
    patches = _write_patches({"gotchas": ["Don't do X", "Don't do Y"]})
    apply_patches(ir, patches)
    assert "Don't do X" in ir.gotchas
    assert "Don't do Y" in ir.gotchas


def test_duplicate_gotcha_not_added():
    ir = IR()
    ir.gotchas.append("Don't do X")
    patches = _write_patches({"gotchas": ["Don't do X"]})
    apply_patches(ir, patches)
    assert ir.gotchas.count("Don't do X") == 1


def test_override_description():
    ir = _make_ir_with_class(description="Old description")
    patches = _write_patches({
        "classes": {"TestClass": {"description": "New description"}}
    })
    apply_patches(ir, patches)
    cls = ir.namespaces["adsk.fusion"]["TestClass"]
    assert cls.description == "New description"


def test_add_method():
    ir = _make_ir_with_class()
    patches = _write_patches({
        "classes": {
            "TestClass": {
                "add_methods": {
                    "doStuff": {
                        "args": [["x", "int"], ["y", "str"]],
                        "returns": "bool",
                    }
                }
            }
        }
    })
    apply_patches(ir, patches)
    cls = ir.namespaces["adsk.fusion"]["TestClass"]
    assert "doStuff" in cls.methods
    m = cls.methods["doStuff"]
    assert m.args == [("x", "int"), ("y", "str")]
    assert m.returns == "bool"


def test_remove_method():
    ir = _make_ir_with_class(
        methods={"badMethod": MethodDef(name="badMethod", returns="int")}
    )
    patches = _write_patches({
        "classes": {"TestClass": {"remove_methods": ["badMethod"]}}
    })
    apply_patches(ir, patches)
    cls = ir.namespaces["adsk.fusion"]["TestClass"]
    assert "badMethod" not in cls.methods


def test_add_property():
    ir = _make_ir_with_class()
    patches = _write_patches({
        "classes": {
            "TestClass": {
                "add_properties": {
                    "myProp": {"type": "str", "read_only": True}
                }
            }
        }
    })
    apply_patches(ir, patches)
    cls = ir.namespaces["adsk.fusion"]["TestClass"]
    assert "myProp" in cls.properties
    assert cls.properties["myProp"].type == "str"
    assert cls.properties["myProp"].read_only is True


def test_remove_property():
    ir = _make_ir_with_class(
        properties={"badProp": PropertyDef(name="badProp", type="int")}
    )
    patches = _write_patches({
        "classes": {"TestClass": {"remove_properties": ["badProp"]}}
    })
    apply_patches(ir, patches)
    cls = ir.namespaces["adsk.fusion"]["TestClass"]
    assert "badProp" not in cls.properties


def test_create_missing_class():
    ir = IR()
    patches = _write_patches({
        "classes": {
            "BrandNewClass": {
                "description": "A new class",
                "add_methods": {
                    "hello": {"returns": "str"}
                },
            }
        }
    })
    apply_patches(ir, patches)
    cls = ir.namespaces["adsk.fusion"]["BrandNewClass"]
    assert cls.description == "A new class"
    assert "hello" in cls.methods


def test_no_patches_file():
    ir = IR()
    apply_patches(ir, "/nonexistent/path.yaml")
    assert ir.gotchas == []


def test_empty_patches_file():
    ir = IR()
    path = _write_patches(None)
    apply_patches(ir, path)
    assert ir.gotchas == []


def test_add_static_method():
    ir = _make_ir_with_class()
    patches = _write_patches({
        "classes": {
            "TestClass": {
                "add_methods": {
                    "factory": {
                        "returns": "TestClass",
                        "static": True,
                    }
                }
            }
        }
    })
    apply_patches(ir, patches)
    m = ir.namespaces["adsk.fusion"]["TestClass"].methods["factory"]
    assert m.static is True


def test_finds_class_across_namespaces():
    ir = IR()
    ir.add_class(ClassDef(name="MyClass", namespace="adsk.core"))
    patches = _write_patches({
        "classes": {"MyClass": {"description": "Patched"}}
    })
    apply_patches(ir, patches)
    assert ir.namespaces["adsk.core"]["MyClass"].description == "Patched"
