# Fusion LAP Converter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python converter that generates `.lap` files from Fusion API type stubs + Autodesk CloudHelp HTML docs.

**Architecture:** Four-stage pipeline -- (1) discover & parse stubs, (2) scrape & enrich from HTML, (3) classify by domain & render `.lap` format, (4) bundle always-load files. Intermediate representation (IR) is a dict of namespaces/classes/methods that both parsers populate.

**Tech Stack:** Python 3.10+, `beautifulsoup4` for HTML parsing, `ast` for `.pyi` parsing, `tiktoken` for token counting, `pyyaml` for config, `click` for CLI, `httpx` for async HTTP fetching.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `fusion_lap/__init__.py`
- Create: `fusion_lap/__main__.py`
- Create: `domains.yaml`
- Create: `CLAUDE.md`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "fusion-lap"
version = "0.1.0"
description = "Compressed LLM-optimized API reference for Autodesk Fusion SDK"
requires-python = ">=3.10"
dependencies = [
    "beautifulsoup4>=4.12",
    "httpx>=0.27",
    "tiktoken>=0.7",
    "pyyaml>=6.0",
    "click>=8.1",
]

[project.scripts]
fusion-lap = "fusion_lap.__main__:cli"
```

**Step 2: Create fusion_lap/__init__.py**

```python
"""Fusion LAP -- compressed LLM-optimized API reference for Autodesk Fusion SDK."""
```

**Step 3: Create fusion_lap/__main__.py with stub CLI**

```python
"""CLI entry point for fusion-lap converter."""

import click


@click.group()
def cli():
    """Fusion LAP converter -- generate .lap files from Fusion API docs."""
    pass


@cli.command()
@click.option("--output", "-o", default="lap/", help="Output directory for .lap files")
@click.option("--no-enrich", is_flag=True, help="Skip HTML enrichment (stubs only)")
@click.option("--domain", help="Rebuild a single domain only")
@click.option("--refresh", is_flag=True, help="Force re-fetch HTML (ignore cache)")
def build(output, no_enrich, domain, refresh):
    """Build .lap files from Fusion API stubs + docs."""
    click.echo(f"Building LAP files to {output}...")
    click.echo("Not yet implemented.")


if __name__ == "__main__":
    cli()
```

**Step 4: Create domains.yaml**

```yaml
# Maps Fusion API classes to domain files via glob patterns.
# Classes not matching any pattern go to fusion-misc.lap.

core:
  - Application
  - Document
  - Base
  - "*Input"
  - "Point*"
  - "Vector*"
  - "Matrix*"
  - ObjectCollection
  - Color
  - Viewport
  - Camera

sketch:
  - "Sketch*"
  - "*Constraint"
  - "*Dimension"
  - "Profile*"
  - "GeometricConstraint*"
  - "DimensionConstraint*"

features:
  - "*Feature"
  - "*Features"
  - "*FeatureInput"
  - ExtentDefinition
  - "*Extent"

bodies:
  - "BRep*"
  - "Mesh*"
  - "TSpline*"
  - SurfaceBody

assembly:
  - Component
  - Occurrence
  - "*Joint*"
  - RigidGroup
  - ContactSet

cam:
  - "CAM*"
  - Operation
  - Toolpath
  - Tool
  - "*Post*"
  - NCProgram
  - Setup

drawing:
  - "Drawing*"
  - "*Annotation*"
  - "*Table"

ui:
  - Command
  - "*CommandInput*"
  - Palette
  - Toolbar
  - "*Event*"
  - UserInterface
  - ToolbarPanel
  - ToolbarTab
```

**Step 5: Create CLAUDE.md**

```markdown
# Fusion API Reference

## Always read these before writing Fusion scripts:
- lap/fusion-base.lap (navigation graph, gotchas, core types)

## Load the relevant domain file when needed:
- lap/fusion-sketch.lap (sketches, curves, constraints, profiles)
- lap/fusion-features.lap (extrude, revolve, loft, sweep, fillet, etc.)
- lap/fusion-bodies.lap (BRep, mesh, T-spline geometry)
- lap/fusion-assembly.lap (components, joints, occurrences)
- lap/fusion-cam.lap (CAM setup, toolpaths, operations)
- lap/fusion-drawing.lap (drawing views, dimensions, annotations)
- lap/fusion-ui.lap (commands, palettes, toolbars, events)

## When writing Fusion scripts:
- Always import: import adsk.core, adsk.fusion, adsk.cam
- Units are centimeters internally
- Check return values for None
- Use the [graph] section in fusion-base.lap to navigate the object model
```

**Step 6: Install in dev mode and verify CLI**

Run: `cd /Users/halletj/git/fusion-lap-sdk && pip install -e .`
Run: `python -m fusion_lap build --help`
Expected: Help text showing build command with --output, --no-enrich, --domain, --refresh options.

**Step 7: Commit**

```bash
git add pyproject.toml fusion_lap/ domains.yaml CLAUDE.md
git commit -m "feat: project scaffolding with CLI stub and domain config"
```

---

### Task 2: Intermediate Representation (IR) Module

**Files:**
- Create: `fusion_lap/ir.py`
- Create: `tests/test_ir.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_ir.py -v`
Expected: FAIL with ModuleNotFoundError (fusion_lap.ir not found)

**Step 3: Write minimal implementation**

```python
"""Intermediate representation for Fusion API classes, methods, and properties."""

from dataclasses import dataclass, field


@dataclass
class PropertyDef:
    name: str
    type: str = ""
    description: str = ""
    read_only: bool = False


@dataclass
class MethodDef:
    name: str
    args: list[tuple[str, str]] = field(default_factory=list)  # [(name, type), ...]
    returns: str = ""
    static: bool = False
    description: str = ""


@dataclass
class ClassDef:
    name: str
    namespace: str = ""
    parent: str = ""
    description: str = ""
    properties: dict[str, PropertyDef] = field(default_factory=dict)
    methods: dict[str, MethodDef] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    is_collection: bool = False
    collection_item_type: str = ""


@dataclass
class EnumDef:
    name: str
    namespace: str = ""
    values: list[str] = field(default_factory=list)
    description: str = ""


class IR:
    """Intermediate representation of the entire Fusion API."""

    def __init__(self):
        self.namespaces: dict[str, dict[str, ClassDef]] = {}
        self.enums: dict[str, dict[str, EnumDef]] = {}
        self.examples: list[dict] = []
        self.gotchas: list[str] = []

    def add_class(self, cls: ClassDef):
        ns = cls.namespace or "_unknown"
        if ns not in self.namespaces:
            self.namespaces[ns] = {}
        self.namespaces[ns][cls.name] = cls

    def add_enum(self, enum: EnumDef):
        ns = enum.namespace or "_unknown"
        if ns not in self.enums:
            self.enums[ns] = {}
        self.enums[ns][enum.name] = enum

    def merge_class(self, enrichment: ClassDef):
        """Merge enrichment data into an existing class. Enrichment fills gaps but doesn't overwrite."""
        ns = enrichment.namespace or "_unknown"
        if ns not in self.namespaces or enrichment.name not in self.namespaces[ns]:
            self.add_class(enrichment)
            return

        existing = self.namespaces[ns][enrichment.name]
        if enrichment.description and not existing.description:
            existing.description = enrichment.description
        if enrichment.parent and not existing.parent:
            existing.parent = enrichment.parent
        for prop_name, prop in enrichment.properties.items():
            if prop_name not in existing.properties:
                existing.properties[prop_name] = prop
            else:
                if prop.description and not existing.properties[prop_name].description:
                    existing.properties[prop_name].description = prop.description
                if prop.type and not existing.properties[prop_name].type:
                    existing.properties[prop_name].type = prop.type
        for method_name, method in enrichment.methods.items():
            if method_name not in existing.methods:
                existing.methods[method_name] = method
            else:
                if method.description and not existing.methods[method_name].description:
                    existing.methods[method_name].description = method.description

    def all_classes(self) -> list[ClassDef]:
        result = []
        for ns_classes in self.namespaces.values():
            result.extend(ns_classes.values())
        return result

    def all_enums(self) -> list[EnumDef]:
        result = []
        for ns_enums in self.enums.values():
            result.extend(ns_enums.values())
        return result
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_ir.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add fusion_lap/ir.py tests/test_ir.py
git commit -m "feat: intermediate representation module with merge support"
```

---

### Task 3: Stub Discovery

**Files:**
- Create: `fusion_lap/discover.py`
- Create: `tests/test_discover.py`

**Step 1: Write the failing test**

```python
"""Tests for stub auto-discovery."""

import os
from unittest.mock import patch
from fusion_lap.discover import find_stubs, StubSource


def test_find_stubs_returns_stub_source():
    result = find_stubs()
    # Should return a StubSource or None, never crash
    assert result is None or isinstance(result, StubSource)


def test_stub_source_has_path_and_kind():
    src = StubSource(path="/fake/path/adsk", kind="fusion_install")
    assert src.path == "/fake/path/adsk"
    assert src.kind == "fusion_install"


def test_find_stubs_respects_fusion_path_env(tmp_path):
    # Create a fake adsk directory with a __init__.pyi
    adsk_dir = tmp_path / "Api" / "Python" / "packages" / "adsk"
    adsk_dir.mkdir(parents=True)
    (adsk_dir / "__init__.pyi").write_text("# stub")

    with patch.dict(os.environ, {"FUSION_PATH": str(tmp_path)}):
        result = find_stubs()
    assert result is not None
    assert result.kind == "fusion_env"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_discover.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
"""Auto-discover Fusion API type stubs from multiple sources."""

import importlib.util
import logging
import os
import platform
from dataclasses import dataclass
from glob import glob
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StubSource:
    path: str
    kind: str  # "pip_fusionscript", "pip_adsk", "fusion_install", "fusion_env"


def find_stubs() -> StubSource | None:
    """Try multiple sources to find Fusion API stubs. Returns first success or None."""
    finders = [
        _try_fusion_env,
        _try_pip_fusionscript_stubs,
        _try_pip_adsk,
        _try_fusion_install,
    ]
    for finder in finders:
        try:
            result = finder()
            if result:
                logger.info(f"Found stubs: {result.kind} at {result.path}")
                return result
        except Exception as e:
            logger.debug(f"{finder.__name__} failed: {e}")
    logger.warning("No stub source found. Will rely on HTML scraping alone.")
    return None


def _try_fusion_env() -> StubSource | None:
    """Check FUSION_PATH environment variable."""
    fusion_path = os.environ.get("FUSION_PATH")
    if not fusion_path:
        return None
    candidates = [
        Path(fusion_path) / "Api" / "Python" / "packages" / "adsk",
        Path(fusion_path) / "adsk",
    ]
    for candidate in candidates:
        if candidate.is_dir() and _has_stubs(candidate):
            return StubSource(path=str(candidate), kind="fusion_env")
    return None


def _try_pip_fusionscript_stubs() -> StubSource | None:
    """Try importing fusionscript-stubs package."""
    spec = importlib.util.find_spec("adsk")
    if spec and spec.origin:
        path = Path(spec.origin).parent
        if _has_stubs(path):
            return StubSource(path=str(path), kind="pip_fusionscript")
    return None


def _try_pip_adsk() -> StubSource | None:
    """Try importing adsk package directly."""
    spec = importlib.util.find_spec("adsk")
    if spec and spec.submodule_search_locations:
        for loc in spec.submodule_search_locations:
            path = Path(loc)
            if path.is_dir():
                return StubSource(path=str(path), kind="pip_adsk")
    return None


def _try_fusion_install() -> StubSource | None:
    """Auto-discover Fusion install directory by platform."""
    system = platform.system()
    home = Path.home()

    if system == "Darwin":
        patterns = [
            str(home / "Library/Application Support/Autodesk/webdeploy/production/*/Autodesk Fusion.app/Contents/Api/Python/packages/adsk"),
            "/Applications/Autodesk Fusion.app/Contents/Api/Python/packages/adsk",
            str(home / "Library/Application Support/Autodesk/webdeploy/production/*/Api/Python/packages/adsk"),
        ]
    elif system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", str(home / "AppData/Local"))
        patterns = [
            f"{local_app_data}/Autodesk/webdeploy/production/*/Api/Python/packages/adsk",
        ]
    elif system == "Linux":
        patterns = [
            str(home / ".local/share/autodesk/webdeploy/production/*/Api/Python/packages/adsk"),
        ]
    else:
        return None

    # Find all matches, pick most recently modified
    all_matches = []
    for pattern in patterns:
        all_matches.extend(glob(pattern))

    if not all_matches:
        return None

    # Sort by modification time, most recent first
    all_matches.sort(key=lambda p: Path(p).stat().st_mtime, reverse=True)
    best = all_matches[0]
    return StubSource(path=best, kind="fusion_install")


def _has_stubs(path: Path) -> bool:
    """Check if a directory looks like it contains adsk stubs."""
    return any(
        (path / f).exists()
        for f in ("__init__.pyi", "__init__.py", "core.pyi", "fusion.pyi")
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_discover.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add fusion_lap/discover.py tests/test_discover.py
git commit -m "feat: auto-discover Fusion API stubs from multiple sources"
```

---

### Task 4: Stub Parser (.pyi -> IR)

**Files:**
- Create: `fusion_lap/stubs.py`
- Create: `tests/test_stubs.py`
- Create: `tests/fixtures/fake_adsk/` (test fixtures)

**Step 1: Create test fixture stubs**

Create `tests/fixtures/fake_adsk/__init__.pyi`:
```python
```

Create `tests/fixtures/fake_adsk/core.pyi`:
```python
class Base:
    def classType() -> str: ...
    @property
    def isValid(self) -> bool: ...
    @property
    def objectType(self) -> str: ...

class Point3D(Base):
    @property
    def x(self) -> float: ...
    @x.setter
    def x(self, value: float) -> None: ...
    @property
    def y(self) -> float: ...
    @property
    def z(self) -> float: ...
    @staticmethod
    def create(x: float = 0, y: float = 0, z: float = 0) -> 'Point3D': ...

class Color(Base):
    @property
    def red(self) -> int: ...
    @property
    def green(self) -> int: ...
    @property
    def blue(self) -> int: ...
    @property
    def opacity(self) -> int: ...
    @staticmethod
    def create(red: int, green: int, blue: int, opacity: int) -> 'Color': ...
```

Create `tests/fixtures/fake_adsk/fusion.pyi`:
```python
import adsk.core

class Feature(adsk.core.Base):
    @property
    def name(self) -> str: ...
    @property
    def isValid(self) -> bool: ...
    @property
    def bodies(self) -> 'BRepBodies': ...
    def deleteMe(self) -> bool: ...

class ExtrudeFeature(Feature):
    @property
    def operation(self) -> 'FeatureOperations': ...
    @property
    def profile(self) -> adsk.core.Base: ...
    def setOneSideExtent(self, extent: 'ExtentDefinition', direction: 'ExtentDirections') -> bool: ...

class FeatureOperations:
    JoinFeatureOperation = 0
    CutFeatureOperation = 1
    IntersectFeatureOperation = 2
    NewBodyFeatureOperation = 3

class ExtrudeFeatures:
    @property
    def count(self) -> int: ...
    def item(self, index: int) -> ExtrudeFeature: ...
    def addSimple(self, profile: adsk.core.Base, distance: adsk.core.Base, operation: FeatureOperations) -> ExtrudeFeature: ...
```

**Step 2: Write the failing test**

```python
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
```

**Step 3: Run test to verify it fails**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_stubs.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 4: Write minimal implementation**

```python
"""Parse Python .pyi stub files into the intermediate representation."""

import ast
import logging
from pathlib import Path

from .ir import IR, ClassDef, MethodDef, PropertyDef, EnumDef

logger = logging.getLogger(__name__)

# Namespace mapping: directory/file names to adsk namespace
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

    # Also try subdirectories (e.g., adsk/core/__init__.pyi)
    for subdir in sorted(stubs_dir.iterdir()):
        if subdir.is_dir() and subdir.name in NAMESPACE_MAP:
            init_pyi = subdir / "__init__.pyi"
            if init_pyi.exists():
                namespace = NAMESPACE_MAP[subdir.name]
                logger.info(f"Parsing {init_pyi} as {namespace}")
                _parse_file(init_pyi, namespace, ir)

    return ir


def _parse_file(path: Path, namespace: str, ir: IR):
    """Parse a single .pyi file and add classes/enums to the IR."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        logger.warning(f"Failed to parse {path}: {e}")
        return

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if _is_enum_class(node):
                enum = _parse_enum(node, namespace)
                ir.add_enum(enum)
            else:
                cls = _parse_class(node, namespace)
                ir.add_class(cls)


def _is_enum_class(node: ast.ClassDef) -> bool:
    """Detect enum-like classes (all assignments, no methods/properties)."""
    has_assignments = False
    has_methods = False
    for item in node.body:
        if isinstance(item, ast.Assign) or isinstance(item, ast.AnnAssign):
            has_assignments = True
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_methods = True
    return has_assignments and not has_methods


def _parse_enum(node: ast.ClassDef, namespace: str) -> EnumDef:
    """Parse an enum-like class into an EnumDef."""
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
    """Parse a class definition into a ClassDef."""
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
                continue  # skip private methods except __init__
            else:
                method = _parse_method(item)
                if method:
                    methods[method.name] = method
                    # Detect collection pattern
                    if method.name == "item" and method.returns:
                        is_collection = True

    cls = ClassDef(
        name=node.name,
        namespace=namespace,
        parent=parent,
        properties=properties,
        methods=methods,
        is_collection=is_collection,
    )

    if is_collection and "item" in methods:
        cls.collection_item_type = methods["item"].returns

    return cls


def _extract_parent(node: ast.ClassDef) -> str:
    """Extract parent class name from class bases."""
    if not node.bases:
        return ""
    base = node.bases[0]
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return ""


def _is_property(node: ast.FunctionDef) -> bool:
    """Check if a function def is decorated with @property."""
    return any(
        (isinstance(d, ast.Name) and d.id == "property")
        or (isinstance(d, ast.Attribute) and d.attr in ("getter", "setter"))
        for d in node.decorator_list
    )


def _is_setter(node: ast.FunctionDef) -> bool:
    """Check if a function def is a property setter."""
    return any(
        isinstance(d, ast.Attribute) and d.attr == "setter"
        for d in node.decorator_list
    )


def _parse_property(node: ast.FunctionDef) -> PropertyDef | None:
    """Parse a @property-decorated function into a PropertyDef."""
    if _is_setter(node):
        return None  # skip setters, they don't add new info
    return_type = _annotation_to_str(node.returns) if node.returns else ""
    return PropertyDef(
        name=node.name,
        type=return_type,
        read_only=True,  # will be updated if setter found
    )


def _parse_method(node: ast.FunctionDef) -> MethodDef | None:
    """Parse a function def into a MethodDef."""
    is_static = any(
        isinstance(d, ast.Name) and d.id == "staticmethod"
        for d in node.decorator_list
    )

    args = []
    for arg in node.args.args:
        if arg.arg == "self":
            continue
        arg_type = _annotation_to_str(arg.annotation) if arg.annotation else ""
        args.append((arg.arg, arg_type))

    return_type = _annotation_to_str(node.returns) if node.returns else ""

    return MethodDef(
        name=node.name,
        args=args,
        returns=return_type,
        static=is_static,
    )


def _annotation_to_str(node: ast.expr | None) -> str:
    """Convert an AST annotation node to a string type name."""
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
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_stubs.py -v`
Expected: All 8 tests PASS

**Step 6: Commit**

```bash
git add fusion_lap/stubs.py tests/test_stubs.py tests/fixtures/
git commit -m "feat: parse .pyi stub files into intermediate representation"
```

---

### Task 5: HTML Scraper

**Files:**
- Create: `fusion_lap/scraper.py`
- Create: `tests/test_scraper.py`
- Create: `tests/fixtures/html/` (cached HTML test fixtures)

**Step 1: Create HTML test fixtures**

Create `tests/fixtures/html/ExtrudeFeature.htm` with representative content:

```html
<html>
<body>
<h1>ExtrudeFeature Object</h1>
<p>Derived from: <a href="Feature.htm">Feature</a> Object</p>
<p>An extrude feature in a design.</p>
<h2>Methods</h2>
<table>
<tr><td><a href="ExtrudeFeature_deleteMe.htm">deleteMe</a></td><td>Deletes this feature.</td></tr>
<tr><td><a href="ExtrudeFeature_setOneSideExtent.htm">setOneSideExtent</a></td><td>Sets the extent for one side.</td></tr>
</table>
<h2>Properties</h2>
<table>
<tr><td><a href="ExtrudeFeature_operation.htm">operation</a></td><td>Gets and sets the feature operation type.</td></tr>
<tr><td><a href="ExtrudeFeature_profile.htm">profile</a></td><td>Gets and sets the profile used by the extrusion.</td></tr>
</table>
</body>
</html>
```

**Step 2: Write the failing test**

```python
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
```

**Step 3: Run test to verify it fails**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_scraper.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 4: Write minimal implementation**

```python
"""Scrape Autodesk CloudHelp HTML for Fusion API class documentation."""

import hashlib
import logging
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from .ir import ClassDef, MethodDef, PropertyDef

logger = logging.getLogger(__name__)

BASE_URL = "https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files"
CACHE_DIR = Path.home() / ".cache" / "fusion-lap" / "html"


def parse_class_page(class_name: str, html: str) -> ClassDef:
    """Parse a single class HTML page into a ClassDef (descriptions only, no types)."""
    soup = BeautifulSoup(html, "html.parser")

    # Extract parent from "Derived from: X Object" pattern
    parent = ""
    for p in soup.find_all("p"):
        text = p.get_text()
        if "Derived from:" in text:
            link = p.find("a")
            if link:
                parent = link.get_text().strip()
            break

    # Extract description: first <p> that isn't the derivation line
    description = ""
    for p in soup.find_all("p"):
        text = p.get_text().strip()
        if text and "Derived from:" not in text and "Defined in" not in text:
            description = text
            break

    # Extract methods and properties from tables following h2 headers
    methods = {}
    properties = {}
    current_section = ""

    for element in soup.find_all(["h2", "table"]):
        if element.name == "h2":
            current_section = element.get_text().strip().lower()
        elif element.name == "table":
            for row in element.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    name_cell = cells[0]
                    desc_cell = cells[1]
                    link = name_cell.find("a")
                    name = link.get_text().strip() if link else name_cell.get_text().strip()
                    desc = desc_cell.get_text().strip()

                    if "method" in current_section:
                        methods[name] = MethodDef(name=name, description=desc)
                    elif "propert" in current_section:
                        read_only = "Gets and sets" not in desc
                        properties[name] = PropertyDef(
                            name=name, description=desc, read_only=read_only
                        )

    return ClassDef(
        name=class_name,
        parent=parent,
        description=description,
        methods=methods,
        properties=properties,
    )


def fetch_class_page(class_name: str, refresh: bool = False) -> str | None:
    """Fetch a class page from CloudHelp, with local caching."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{class_name}.htm"

    if cache_file.exists() and not refresh:
        return cache_file.read_text(encoding="utf-8")

    url = f"{BASE_URL}/{class_name}.htm"
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30)
        if resp.status_code == 200:
            html = resp.text
            cache_file.write_text(html, encoding="utf-8")
            return html
        else:
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return None
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def scrape_class_index(refresh: bool = False) -> list[str]:
    """Fetch the reference manual index and extract all class names."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "_index.htm"

    if cache_file.exists() and not refresh:
        html = cache_file.read_text(encoding="utf-8")
    else:
        url = f"{BASE_URL}/ReferenceManual_UM.htm"
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=30)
            html = resp.text
            cache_file.write_text(html, encoding="utf-8")
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch index: {e}")
            return []

    # Extract class names from links matching the pattern ClassName.htm
    soup = BeautifulSoup(html, "html.parser")
    class_names = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]
        match = re.match(r"^([A-Z][A-Za-z0-9]+)\.htm$", href)
        if match:
            class_names.add(match.group(1))

    return sorted(class_names)
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_scraper.py -v`
Expected: All 3 tests PASS

**Step 6: Commit**

```bash
git add fusion_lap/scraper.py tests/test_scraper.py tests/fixtures/html/
git commit -m "feat: HTML scraper for Autodesk CloudHelp class pages"
```

---

### Task 6: Enrichment (Merge Stubs + HTML)

**Files:**
- Create: `fusion_lap/enrich.py`
- Create: `tests/test_enrich.py`

**Step 1: Write the failing test**

```python
"""Tests for enrichment (merging stubs + scraped HTML)."""

from fusion_lap.enrich import enrich_ir
from fusion_lap.ir import IR, ClassDef, MethodDef, PropertyDef


def test_enrich_adds_descriptions():
    # Simulate stubs IR (has types, no descriptions)
    ir = IR()
    ir.add_class(ClassDef(
        name="ExtrudeFeature",
        namespace="adsk.fusion",
        parent="Feature",
        methods={"deleteMe": MethodDef(name="deleteMe", returns="bool")},
        properties={"operation": PropertyDef(name="operation", type="FeatureOperations")},
    ))

    # Simulate scraped data
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
    assert cls.methods["deleteMe"].returns == "bool"  # preserved from stubs
    assert cls.properties["operation"].description == "Gets the operation type."
    assert cls.properties["operation"].type == "FeatureOperations"  # preserved from stubs


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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_enrich.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
"""Enrich stub-derived IR with descriptions from scraped HTML."""

import logging

from .ir import IR, ClassDef

logger = logging.getLogger(__name__)


def enrich_ir(ir: IR, scraped: dict[str, ClassDef]):
    """Merge scraped class data into the existing IR.

    Scraped data fills in descriptions and adds classes not found in stubs.
    Stubs retain authority over types, inheritance, and signatures.
    """
    for class_name, scraped_cls in scraped.items():
        # Find existing class in any namespace
        found = False
        for ns_classes in ir.namespaces.values():
            if class_name in ns_classes:
                ir.merge_class(scraped_cls)
                found = True
                break

        if not found:
            # Class exists in HTML but not stubs -- add it with unknown namespace
            if not scraped_cls.namespace:
                scraped_cls.namespace = _guess_namespace(class_name)
            ir.add_class(scraped_cls)
            logger.info(f"Added {class_name} from HTML (not in stubs)")


def _guess_namespace(class_name: str) -> str:
    """Guess namespace from class name patterns."""
    fusion_prefixes = (
        "Sketch", "Feature", "BRep", "Mesh", "TSpline", "Component",
        "Occurrence", "Joint", "Extrude", "Revolve", "Loft", "Sweep",
        "Fillet", "Chamfer", "Shell", "Hole", "Thread", "Pattern",
        "Design", "Timeline", "Profile",
    )
    cam_prefixes = ("CAM", "Setup", "Operation", "Toolpath", "Tool", "NC", "Post")

    for prefix in cam_prefixes:
        if class_name.startswith(prefix):
            return "adsk.cam"
    for prefix in fusion_prefixes:
        if class_name.startswith(prefix):
            return "adsk.fusion"
    return "adsk.core"
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_enrich.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add fusion_lap/enrich.py tests/test_enrich.py
git commit -m "feat: enrich stubs IR with scraped HTML descriptions"
```

---

### Task 7: LAP Renderer (IR -> .lap files)

**Files:**
- Create: `fusion_lap/render.py`
- Create: `tests/test_render.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_render.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
"""Render IR into .lap format files."""

import fnmatch
import logging

from .ir import IR, ClassDef, EnumDef

logger = logging.getLogger(__name__)


def render_domain(ir: IR, domain_name: str, patterns: list[str]) -> str:
    """Render all classes/enums matching patterns into a .lap domain file."""
    lines = [f"# fusion-{domain_name}.lap", ""]

    # Collect matching enums
    matching_enums = []
    for enum in ir.all_enums():
        if _matches_any(enum.name, patterns):
            matching_enums.append(enum)

    # Collect matching classes
    matching_classes = []
    for cls in ir.all_classes():
        if _matches_any(cls.name, patterns):
            matching_classes.append(cls)

    # Render types section (enums)
    if matching_enums:
        lines.append("[types]")
        for enum in sorted(matching_enums, key=lambda e: e.name):
            lines.append(f"{enum.name}: {' | '.join(enum.values)}")
        lines.append("")

    # Render classes section
    if matching_classes:
        lines.append("[classes]")
        for cls in sorted(matching_classes, key=lambda c: c.name):
            lines.extend(_render_class(cls))
            lines.append("")

    return "\n".join(lines)


def render_graph(ir: IR) -> str:
    """Render the [graph] section from the IR."""
    lines = ["# fusion-graph.lap", "", "[graph]"]

    # Find Application class and render its property tree
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


def _render_class(cls: ClassDef) -> list[str]:
    """Render a single class definition."""
    lines = []

    # Class header
    if cls.is_collection and cls.collection_item_type:
        header = f"{cls.name} *collection<{cls.collection_item_type}>"
    elif cls.parent:
        header = f"{cls.name} : {cls.parent}"
    else:
        header = cls.name
    lines.append(header)

    # Description (one line, if short enough)
    if cls.description and len(cls.description) < 100:
        lines.append(f"  # {cls.description}")

    # Properties
    for prop_name in sorted(cls.properties):
        prop = cls.properties[prop_name]
        type_str = f": {prop.type}" if prop.type else ""
        lines.append(f"  {prop_name}{type_str}")

    # Methods
    for method_name in sorted(cls.methods):
        method = cls.methods[method_name]
        if method_name == "item" and cls.is_collection:
            continue  # skip item() on collections, covered by *collection shorthand
        args_str = ", ".join(f"{name}: {typ}" for name, typ in method.args)
        returns_str = f" -> {method.returns}" if method.returns else ""
        static_prefix = "@static " if method.static else ""
        lines.append(f"  {static_prefix}{method_name}({args_str}){returns_str}")

    return lines


def _matches_any(name: str, patterns: list[str]) -> bool:
    """Check if a class/enum name matches any glob pattern in the list."""
    return any(fnmatch.fnmatch(name, p) for p in patterns)
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_render.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add fusion_lap/render.py tests/test_render.py
git commit -m "feat: LAP renderer converts IR to .lap format files"
```

---

### Task 8: Build Pipeline (Wire It All Together)

**Files:**
- Modify: `fusion_lap/__main__.py`
- Create: `fusion_lap/build.py`
- Create: `tests/test_build.py`

**Step 1: Write the failing test**

```python
"""Tests for the full build pipeline."""

from pathlib import Path
from fusion_lap.build import build_lap_files

FIXTURES = Path(__file__).parent / "fixtures" / "fake_adsk"


def test_build_produces_lap_files(tmp_path):
    build_lap_files(
        output_dir=str(tmp_path),
        stubs_path=str(FIXTURES),
        no_enrich=True,
    )
    # Should produce at least fusion-base.lap
    assert (tmp_path / "fusion-base.lap").exists()
    assert (tmp_path / "fusion-graph.lap").exists()
    assert (tmp_path / "fusion-gotchas.lap").exists()


def test_build_base_contains_graph(tmp_path):
    build_lap_files(
        output_dir=str(tmp_path),
        stubs_path=str(FIXTURES),
        no_enrich=True,
    )
    base = (tmp_path / "fusion-base.lap").read_text()
    assert "[graph]" in base
    assert "[gotchas]" in base


def test_build_domain_files_contain_classes(tmp_path):
    build_lap_files(
        output_dir=str(tmp_path),
        stubs_path=str(FIXTURES),
        no_enrich=True,
    )
    # Our fixture has ExtrudeFeature which should land in features domain
    features_file = tmp_path / "fusion-features.lap"
    if features_file.exists():
        content = features_file.read_text()
        assert "ExtrudeFeature" in content
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_build.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
"""Full build pipeline: discover stubs, scrape, enrich, render, bundle."""

import logging
from pathlib import Path

import yaml

from .discover import find_stubs
from .enrich import enrich_ir
from .ir import IR
from .render import render_domain, render_gotchas, render_graph, render_meta
from .scraper import fetch_class_page, parse_class_page, scrape_class_index
from .stubs import parse_stubs

logger = logging.getLogger(__name__)

DEFAULT_GOTCHAS = [
    "Units are always centimeters internally, regardless of UI settings",
    "Always check return values for None -- operations fail silently",
    "Use design.designType = ParametricDesignType before parametric features",
    "Input objects must be fully configured before calling .add()",
    "Sketch profiles only available after geometry is fully closed",
    "Point3D.create() takes cm, not mm or inches",
    "Collections are 0-indexed, use .item(i) or [i]",
]


def build_lap_files(
    output_dir: str = "lap",
    stubs_path: str | None = None,
    no_enrich: bool = False,
    domain_filter: str | None = None,
    refresh: bool = False,
    domains_yaml: str = "domains.yaml",
):
    """Run the full build pipeline."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Stage 1: Get stubs
    if stubs_path:
        logger.info(f"Using provided stubs path: {stubs_path}")
        ir = parse_stubs(stubs_path)
    else:
        source = find_stubs()
        if source:
            ir = parse_stubs(source.path)
        else:
            logger.warning("No stubs found. Building from HTML only.")
            ir = IR()

    # Stage 2: Scrape & enrich
    if not no_enrich:
        logger.info("Scraping Autodesk CloudHelp for descriptions...")
        class_names = scrape_class_index(refresh=refresh)
        scraped = {}
        for class_name in class_names:
            html = fetch_class_page(class_name, refresh=refresh)
            if html:
                scraped[class_name] = parse_class_page(class_name, html)
        enrich_ir(ir, scraped)
        logger.info(f"Enriched with {len(scraped)} classes from HTML")

    # Add default gotchas
    ir.gotchas = DEFAULT_GOTCHAS

    # Stage 3: Classify & render
    domains = _load_domains(domains_yaml)

    for domain_name, patterns in domains.items():
        if domain_filter and domain_name != domain_filter:
            continue
        content = render_domain(ir, domain_name, patterns)
        filepath = out / f"fusion-{domain_name}.lap"
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Wrote {filepath}")

    # Render always-load files
    graph_content = render_graph(ir)
    (out / "fusion-graph.lap").write_text(graph_content, encoding="utf-8")

    gotchas_content = render_gotchas(ir)
    (out / "fusion-gotchas.lap").write_text(gotchas_content, encoding="utf-8")

    meta_content = render_meta()
    core_file = out / "fusion-core.lap"
    if core_file.exists():
        # Prepend meta to core
        existing = core_file.read_text(encoding="utf-8")
        core_file.write_text(meta_content + "\n" + existing, encoding="utf-8")

    # Stage 4: Bundle
    base_parts = []
    for name in ["fusion-graph.lap", "fusion-gotchas.lap", "fusion-core.lap"]:
        part_file = out / name
        if part_file.exists():
            base_parts.append(part_file.read_text(encoding="utf-8"))
    base_content = "\n".join(base_parts)
    (out / "fusion-base.lap").write_text(base_content, encoding="utf-8")
    logger.info(f"Wrote {out / 'fusion-base.lap'}")

    # Print summary
    _print_summary(out)


def _load_domains(domains_yaml: str) -> dict[str, list[str]]:
    """Load domain-to-patterns mapping from YAML."""
    path = Path(domains_yaml)
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"{domains_yaml} not found, using default domains")
        return {
            "core": ["Application", "Document", "Base", "*Input", "Point*", "Vector*", "Matrix*"],
            "features": ["*Feature", "*Features", "*FeatureInput"],
            "sketch": ["Sketch*", "*Constraint", "*Dimension", "Profile*"],
            "bodies": ["BRep*", "Mesh*", "TSpline*"],
            "assembly": ["Component", "Occurrence", "*Joint*"],
            "cam": ["CAM*", "Operation", "Toolpath", "Tool"],
            "ui": ["Command", "*CommandInput*", "Palette", "Toolbar", "*Event*"],
        }


def _print_summary(out: Path):
    """Print token count summary for generated files."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
    except ImportError:
        logger.info("Install tiktoken for token count summary")
        enc = None

    total_tokens = 0
    print("\n--- Build Summary ---")
    print(f"{'File':<30} {'Size':>8} {'Tokens':>8}")
    print("-" * 50)
    for lap_file in sorted(out.glob("*.lap")):
        content = lap_file.read_text(encoding="utf-8")
        size = len(content)
        tokens = len(enc.encode(content)) if enc else 0
        total_tokens += tokens
        token_str = str(tokens) if enc else "n/a"
        print(f"{lap_file.name:<30} {size:>7}B {token_str:>8}")
    if enc:
        print("-" * 50)
        print(f"{'Total':<30} {'':>8} {total_tokens:>8}")
    print()
```

**Step 4: Wire into CLI**

Update `fusion_lap/__main__.py`:

```python
"""CLI entry point for fusion-lap converter."""

import logging

import click

from .build import build_lap_files


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose):
    """Fusion LAP converter -- generate .lap files from Fusion API docs."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@cli.command()
@click.option("--output", "-o", default="lap/", help="Output directory for .lap files")
@click.option("--no-enrich", is_flag=True, help="Skip HTML enrichment (stubs only)")
@click.option("--domain", help="Rebuild a single domain only")
@click.option("--refresh", is_flag=True, help="Force re-fetch HTML (ignore cache)")
@click.option("--stubs", help="Path to adsk stubs directory (auto-detected if omitted)")
def build(output, no_enrich, domain, refresh, stubs):
    """Build .lap files from Fusion API stubs + docs."""
    build_lap_files(
        output_dir=output,
        stubs_path=stubs,
        no_enrich=no_enrich,
        domain_filter=domain,
        refresh=refresh,
    )


if __name__ == "__main__":
    cli()
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_build.py -v`
Expected: All 3 tests PASS

**Step 6: Run full pipeline with fixture stubs**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m fusion_lap build -o /tmp/lap-test --no-enrich --stubs tests/fixtures/fake_adsk`
Expected: Build summary table printed, .lap files created in /tmp/lap-test/

**Step 7: Commit**

```bash
git add fusion_lap/build.py fusion_lap/__main__.py tests/test_build.py
git commit -m "feat: full build pipeline wiring stubs, enrichment, rendering, and bundling"
```

---

### Task 9: MCP Server

**Files:**
- Create: `fusion_lap/mcp_server.py`
- Create: `tests/test_mcp_server.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_mcp_server.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
"""MCP server exposing Fusion LAP files as tools."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_LAP_DIR = Path(__file__).parent.parent / "lap"


def lookup_domain(domain: str, lap_dir: str | None = None) -> str:
    """Return the full content of a domain .lap file."""
    d = Path(lap_dir) if lap_dir else DEFAULT_LAP_DIR
    filepath = d / f"fusion-{domain}.lap"
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return f"Domain '{domain}' not found. Available: {', '.join(_list_domains(d))}"


def search_lap(query: str, lap_dir: str | None = None) -> str:
    """Search across all .lap files for a query string."""
    d = Path(lap_dir) if lap_dir else DEFAULT_LAP_DIR
    results = []
    for lap_file in sorted(d.glob("fusion-*.lap")):
        content = lap_file.read_text(encoding="utf-8")
        matching_lines = []
        for i, line in enumerate(content.splitlines(), 1):
            if query.lower() in line.lower():
                matching_lines.append(f"  L{i}: {line.strip()}")
        if matching_lines:
            results.append(f"--- {lap_file.name} ---")
            results.extend(matching_lines[:10])  # cap per file
    return "\n".join(results) if results else f"No matches for '{query}'"


def get_graph(lap_dir: str | None = None) -> str:
    """Return the navigation graph."""
    d = Path(lap_dir) if lap_dir else DEFAULT_LAP_DIR
    filepath = d / "fusion-graph.lap"
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return "fusion-graph.lap not found."


def _list_domains(d: Path) -> list[str]:
    """List available domain names."""
    domains = []
    for f in sorted(d.glob("fusion-*.lap")):
        name = f.stem.replace("fusion-", "")
        if name not in ("base", "graph", "gotchas"):
            domains.append(name)
    return domains
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_mcp_server.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add fusion_lap/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: MCP server tool functions for LAP file access"
```

---

### Task 10: End-to-End Test with Real Stubs

**Files:**
- Create: `tests/test_e2e.py`

**Step 1: Write e2e test**

```python
"""End-to-end test: run full build and validate output."""

from pathlib import Path
from fusion_lap.build import build_lap_files

FIXTURES = Path(__file__).parent / "fixtures" / "fake_adsk"


def test_e2e_build_and_validate(tmp_path):
    """Build from fixture stubs, validate all expected outputs."""
    build_lap_files(
        output_dir=str(tmp_path),
        stubs_path=str(FIXTURES),
        no_enrich=True,
    )

    # fusion-base.lap must exist and contain all three sections
    base = (tmp_path / "fusion-base.lap").read_text()
    assert "[graph]" in base
    assert "[gotchas]" in base
    assert "centimeters" in base

    # At least one domain file must contain our fixture classes
    all_content = ""
    for lap_file in tmp_path.glob("fusion-*.lap"):
        all_content += lap_file.read_text()

    assert "ExtrudeFeature" in all_content
    assert "Point3D" in all_content
    assert "FeatureOperations" in all_content

    # Verify no empty domain files (besides potentially misc)
    for lap_file in tmp_path.glob("fusion-*.lap"):
        content = lap_file.read_text()
        assert len(content) > 10, f"{lap_file.name} is suspiciously empty"
```

**Step 2: Run test**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/test_e2e.py -v`
Expected: PASS

**Step 3: Run all tests**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: end-to-end build pipeline validation"
```

---

### Task 11: Generate Initial LAP Files

**Step 1: Run the converter for real**

If Fusion is installed locally:
Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m fusion_lap build -o lap/ -v`

If Fusion is not installed (stubs-only mode with enrichment):
Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m fusion_lap build -o lap/ -v`
(It will fall through to HTML-only if no stubs found)

If nothing works, use fixture stubs as proof of concept:
Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m fusion_lap build -o lap/ --stubs tests/fixtures/fake_adsk --no-enrich -v`

**Step 2: Review build summary**

Check the token count summary table. Verify domain files look reasonable.

**Step 3: Spot-check fusion-base.lap**

Run: `head -50 lap/fusion-base.lap`
Expected: Contains [graph], [gotchas], and [meta] sections with real content.

**Step 4: Commit generated files**

```bash
git add lap/ CLAUDE.md
git commit -m "feat: initial generated LAP files for Fusion API"
```

---

### Task 12: Final Integration Test

**Step 1: Verify CLAUDE.md references work**

Run: `cat CLAUDE.md`
Verify all referenced .lap files exist in lap/ directory.

**Step 2: Test MCP tool functions manually**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -c "from fusion_lap.mcp_server import lookup_domain, search_lap; print(search_lap('Extrude'))"`
Expected: Prints matching lines from fusion-features.lap.

**Step 3: Run full test suite one final time**

Run: `cd /Users/halletj/git/fusion-lap-sdk && python -m pytest tests/ -v`
Expected: All tests PASS.

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final integration verification"
```
