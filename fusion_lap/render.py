"""Render IR into .lap format files."""

import fnmatch
import logging

from .ir import IR, ClassDef, EnumDef

logger = logging.getLogger(__name__)


def render_domain(ir: IR, domain_name: str, patterns: list[str]) -> str:
    """Render all classes/enums matching patterns into a .lap domain file."""
    lines = [f"# fusion-{domain_name}.lap", ""]

    matching_enums = []
    for enum in ir.all_enums():
        if _matches_any(enum.name, patterns):
            matching_enums.append(enum)

    matching_classes = []
    for cls in ir.all_classes():
        if _matches_any(cls.name, patterns):
            matching_classes.append(cls)

    if matching_enums:
        lines.append("[types]")
        for enum in sorted(matching_enums, key=lambda e: e.name):
            lines.append(f"{enum.name}: {' | '.join(enum.values)}")
        lines.append("")

    if matching_classes:
        lines.append("[classes]")
        for cls in sorted(matching_classes, key=lambda c: c.name):
            lines.extend(_render_class(cls))
            lines.append("")

    return "\n".join(lines)


def render_graph(ir: IR) -> str:
    """Render the [graph] section from the IR."""
    lines = ["# fusion-graph.lap", "", "[graph]"]

    app = None
    for cls in ir.all_classes():
        if cls.name == "Application":
            app = cls
            break

    if app:
        lines.append("Application")
        for prop_name, prop in sorted(app.properties.items()):
            lines.append(f"  .{prop_name} -> {prop.type}")
    else:
        lines.append("# Application class not found in IR")

    lines.append("")
    return "\n".join(lines)


def render_gotchas(ir: IR) -> str:
    """Render the [gotchas] section."""
    lines = ["# fusion-gotchas.lap", "", "[gotchas]"]
    for gotcha in ir.gotchas:
        if not gotcha.startswith("- "):
            gotcha = f"- {gotcha}"
        lines.append(gotcha)
    lines.append("")
    return "\n".join(lines)


def render_meta() -> str:
    """Render the [meta] section."""
    return """[meta]
api: Autodesk Fusion
lang: python
namespace: adsk.core, adsk.fusion, adsk.cam
import: import adsk.core, adsk.fusion, adsk.cam
"""


def render_remaining(ir: IR, all_domain_patterns: dict[str, list[str]]) -> str:
    """Render all classes/enums that don't match any domain pattern into fusion-misc.lap."""
    # Collect all patterns across all domains
    all_patterns = []
    for patterns in all_domain_patterns.values():
        all_patterns.extend(patterns)

    unmatched_enums = [e for e in ir.all_enums() if not _matches_any(e.name, all_patterns)]
    unmatched_classes = [c for c in ir.all_classes() if not _matches_any(c.name, all_patterns)]

    lines = ["# fusion-misc.lap", ""]

    if unmatched_enums:
        lines.append("[types]")
        for enum in sorted(unmatched_enums, key=lambda e: e.name):
            lines.append(f"{enum.name}: {' | '.join(enum.values)}")
        lines.append("")

    if unmatched_classes:
        lines.append("[classes]")
        for cls in sorted(unmatched_classes, key=lambda c: c.name):
            lines.extend(_render_class(cls))
            lines.append("")

    return "\n".join(lines)


def _render_class(cls: ClassDef) -> list[str]:
    """Render a single class definition."""
    lines = []

    if cls.is_collection and cls.collection_item_type:
        header = f"{cls.name} *collection<{cls.collection_item_type}>"
    elif cls.parent:
        header = f"{cls.name} : {cls.parent}"
    else:
        header = cls.name
    lines.append(header)

    if cls.description and len(cls.description) < 100:
        lines.append(f"  # {cls.description}")

    for prop_name in sorted(cls.properties):
        prop = cls.properties[prop_name]
        type_str = f": {prop.type}" if prop.type else ""
        lines.append(f"  {prop_name}{type_str}")

    for method_name in sorted(cls.methods):
        method = cls.methods[method_name]
        if method_name == "item" and cls.is_collection:
            continue
        args_str = ", ".join(f"{name}: {typ}" for name, typ in method.args)
        returns_str = f" -> {method.returns}" if method.returns else ""
        static_prefix = "@static " if method.static else ""
        lines.append(f"  {static_prefix}{method_name}({args_str}){returns_str}")

    return lines


def _matches_any(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)
