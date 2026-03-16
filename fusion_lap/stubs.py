"""Parse Python .pyi stub files into the intermediate representation."""

import ast
import logging
from pathlib import Path

from .ir import IR, ClassDef, MethodDef, PropertyDef, EnumDef

logger = logging.getLogger(__name__)

NAMESPACE_MAP = {
    "core": "adsk.core",
    "fusion": "adsk.fusion",
    "cam": "adsk.cam",
}


def parse_stubs(stubs_path: str) -> IR:
    """Parse all .pyi files under stubs_path into an IR."""
    ir = IR()
    stubs_dir = Path(stubs_path)

    for pyi_file in sorted(stubs_dir.glob("*.pyi")):
        stem = pyi_file.stem
        if stem == "__init__":
            continue
        namespace = NAMESPACE_MAP.get(stem, f"adsk.{stem}")
        logger.info(f"Parsing {pyi_file.name} as {namespace}")
        _parse_file(pyi_file, namespace, ir)

    for subdir in sorted(stubs_dir.iterdir()):
        if subdir.is_dir() and subdir.name in NAMESPACE_MAP:
            init_pyi = subdir / "__init__.pyi"
            if init_pyi.exists():
                namespace = NAMESPACE_MAP[subdir.name]
                _parse_file(init_pyi, namespace, ir)

    return ir


def _parse_file(path: Path, namespace: str, ir: IR):
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        logger.warning(f"Failed to parse {path}: {e}")
        return

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if _is_enum_class(node):
                ir.add_enum(_parse_enum(node, namespace))
            else:
                ir.add_class(_parse_class(node, namespace))


def _is_enum_class(node: ast.ClassDef) -> bool:
    has_assignments = False
    has_methods = False
    for item in node.body:
        if isinstance(item, (ast.Assign, ast.AnnAssign)):
            has_assignments = True
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_methods = True
    return has_assignments and not has_methods


def _parse_enum(node: ast.ClassDef, namespace: str) -> EnumDef:
    values = []
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    values.append(target.id)
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            values.append(item.target.id)
    return EnumDef(name=node.name, namespace=namespace, values=values)


def _parse_class(node: ast.ClassDef, namespace: str) -> ClassDef:
    parent = _extract_parent(node)
    properties = {}
    methods = {}
    is_collection = False

    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            if _is_property(item):
                prop = _parse_property(item)
                if prop:
                    properties[prop.name] = prop
            elif item.name.startswith("_") and item.name != "__init__":
                continue
            else:
                method = _parse_method(item)
                if method:
                    methods[method.name] = method
                    if method.name == "item" and method.returns:
                        is_collection = True

    cls = ClassDef(
        name=node.name, namespace=namespace, parent=parent,
        properties=properties, methods=methods, is_collection=is_collection,
    )
    if is_collection and "item" in methods:
        cls.collection_item_type = methods["item"].returns
    return cls


def _extract_parent(node: ast.ClassDef) -> str:
    if not node.bases:
        return ""
    base = node.bases[0]
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return ""


def _is_property(node: ast.FunctionDef) -> bool:
    return any(
        (isinstance(d, ast.Name) and d.id == "property")
        or (isinstance(d, ast.Attribute) and d.attr in ("getter", "setter"))
        for d in node.decorator_list
    )


def _is_setter(node: ast.FunctionDef) -> bool:
    return any(isinstance(d, ast.Attribute) and d.attr == "setter" for d in node.decorator_list)


def _parse_property(node: ast.FunctionDef) -> PropertyDef | None:
    if _is_setter(node):
        return None
    return_type = _annotation_to_str(node.returns) if node.returns else ""
    return PropertyDef(name=node.name, type=return_type, read_only=True)


def _parse_method(node: ast.FunctionDef) -> MethodDef | None:
    is_static = any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in node.decorator_list)
    args = []
    for arg in node.args.args:
        if arg.arg == "self":
            continue
        arg_type = _annotation_to_str(arg.annotation) if arg.annotation else ""
        args.append((arg.arg, arg_type))
    return_type = _annotation_to_str(node.returns) if node.returns else ""
    return MethodDef(name=node.name, args=args, returns=return_type, static=is_static)


def _annotation_to_str(node) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        base = _annotation_to_str(node.value)
        inner = _annotation_to_str(node.slice)
        return f"{base}[{inner}]"
    return ast.dump(node)
