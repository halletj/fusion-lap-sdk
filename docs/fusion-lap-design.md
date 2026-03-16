# Fusion LAP Design

A compressed, LLM-optimized API reference format for the Autodesk Fusion SDK.
Inspired by [LAPIS](https://arxiv.org/abs/2602.18541), extended for object-oriented
desktop SDKs.

## Goals

1. Compress the Fusion API reference to ~80-90K tokens (from ~500K+ raw docs)
2. Partition into domain files for selective loading (~8K always-load baseline)
3. Preserve enough detail for LLMs to generate correct Fusion scripts
4. Auto-generate from type stubs + Autodesk HTML docs via a Python converter
5. Ship generated `.lap` files in the repo so consumers never run the converter

## Format Spec

### File Extension

`.lap` -- plain text, UTF-8.

### Sections

Each `.lap` file contains some or all of these sections in order:

| Section | Purpose |
|---|---|
| `[meta]` | API name, version, namespaces, imports |
| `[patterns]` | Reusable patterns (Collection\<T\>, InputObject conventions) |
| `[types]` | Enums, value types, simple structs |
| `[classes]` | Classes with inheritance, properties, methods |
| `[graph]` | Object graph navigation from Application root |
| `[examples]` | Runnable code snippets for common tasks |
| `[gotchas]` | Common pitfalls and implicit rules |
| `[events]` | Event handler patterns |

### Syntax

#### Meta

```
[meta]
api: Autodesk Fusion
version: 2.0
lang: python
namespace: adsk.core, adsk.fusion, adsk.cam
import: import adsk.core, adsk.fusion, adsk.cam
```

#### Patterns

Declare reusable structural patterns once:

```
[patterns]
*Collection<T>:
  count: int
  item(index: int) -> T
  [index] -> T
  __iter__ -> T

*InputObject:
  # Created via parent collection's .createInput() or similar factory
  # Must be fully configured before passing to .add()
```

#### Types

Enums and value types:

```
[types]
FeatureOperations: JoinFeatureOperation | CutFeatureOperation | IntersectFeatureOperation | NewBodyFeatureOperation

Point3D:
  x: float
  y: float
  z: float
  @static create(x: float, y: float, z: float) -> Point3D

ValueInput:
  @static createByReal(real: float) -> ValueInput
  @static createByString(expression: str) -> ValueInput
```

#### Classes

Inheritance with `:`, properties without parens, methods with parens:

```
[classes]
Feature : Base
  name: str
  isValid: bool
  timelineObject: TimelineObject
  bodies: BRepBodies *collection
  deleteMe() -> bool

ExtrudeFeature : Feature
  extentOne: ExtentDefinition
  operation: FeatureOperations
  startExtent: ExtentDefinition
  setOneSideExtent(extent: ExtentDefinition, direction: ExtentDirections) -> bool
  @static cast(obj: Base) -> ExtrudeFeature
```

Top ~50 most-used classes inline inherited members for LLM convenience.
Other classes reference their parent with `: ParentClass` and show only new members.

Collection classes use shorthand:

```
ExtrudeFeatures *collection<ExtrudeFeature>
  addSimple(profile: Profile, distance: ValueInput, operation: FeatureOperations) -> ExtrudeFeature
  createInput(profile: Profile, operation: FeatureOperations) -> ExtrudeFeatureInput
```

#### Graph

Compact navigation tree from Application root:

```
[graph]
Application
  .activeDocument -> Document
    .design -> Design
      .designType: DesignTypes
      .rootComponent -> Component
        .sketches -> Sketches *coll
          .add(planarEntity) -> Sketch
        .features -> Features
          .extrudeFeatures -> ExtrudeFeatures *coll
          .revolveFeatures -> RevolveFeatures *coll
          .filletFeatures -> FilletFeatures *coll
        .bRepBodies -> BRepBodies *coll
        .occurrences -> Occurrences *coll
        .joints -> Joints *coll
        .constructionPlanes -> ConstructionPlanes *coll
  .userInterface -> UserInterface
    .commandDefinitions -> CommandDefinitions
    .palettes -> Palettes
```

#### Examples

Runnable Python snippets for common tasks:

```
[examples]
basic_extrude "Create an extruded box"
  sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
  lines = sketch.sketchCurves.sketchLines
  lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(5, 5, 0))
  profile = sketch.profiles.item(0)
  dist = adsk.core.ValueInput.createByReal(2.0)
  ext = rootComp.features.extrudeFeatures.addSimple(
    profile, dist, adsk.fusion.FeatureOperations.JoinFeatureOperation)

input_object_pattern "Create feature via input object"
  extInput = rootComp.features.extrudeFeatures.createInput(
    profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
  extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3.0))
  ext = rootComp.features.extrudeFeatures.add(extInput)
```

#### Gotchas

```
[gotchas]
- Units are always centimeters internally, regardless of UI settings
- Always check return values for None -- operations fail silently
- Use design.designType = ParametricDesignType before parametric features
- Input objects must be fully configured before calling .add()
- Sketch profiles only available after geometry is fully closed
- Point3D.create() takes cm, not mm or inches
- Collections are 0-indexed, use .item(i) or [i]
```

#### Events

```
[events]
CommandCreatedEventHandler
  ! When a command is created in the UI
  > args: CommandCreatedEventArgs
    .command -> Command
    .command.commandInputs -> CommandInputs

InputChangedEventHandler
  ! When a command input value changes
  > args: InputChangedEventArgs
    .input -> CommandInput
```

## Domain Partitioning

Generated `.lap` files, split by functional domain:

| File | Contents | Est. Tokens |
|---|---|---|
| `fusion-graph.lap` | Navigation tree only (always-load) | ~2K |
| `fusion-gotchas.lap` | Common pitfalls (always-load) | ~1K |
| `fusion-core.lap` | Application, Document, Base, Point3D, Vector3D, Matrix3D, ValueInput, ObjectCollection | ~5K |
| `fusion-sketch.lap` | Sketch, SketchCurves, SketchLines, SketchCircles, SketchArcs, SketchPoints, Constraints, Dimensions, Profiles | ~15K |
| `fusion-features.lap` | Extrude, Revolve, Loft, Sweep, Fillet, Chamfer, Shell, Draft, Hole, Thread, Pattern, Mirror, Combine, Split | ~20K |
| `fusion-bodies.lap` | BRepBody, BRepFace, BRepEdge, BRepVertex, MeshBody, TSplineBody | ~10K |
| `fusion-assembly.lap` | Component, Occurrence, Joint, JointOrigin, AsBuiltJoint, RigidGroup | ~10K |
| `fusion-cam.lap` | CAMSetup, Operation, Toolpath, Tool, PostProcess, NCProgram | ~12K |
| `fusion-drawing.lap` | DrawingDocument, DrawingView, Dimensions, Annotations, Tables | ~8K |
| `fusion-ui.lap` | Command, CommandInputs, Palette, Toolbar, CustomEvent, UserInterface | ~8K |
| `fusion-misc.lap` | Uncategorized classes | ~5K |
| **`fusion-base.lap`** | **Bundle: graph + gotchas + core** | **~8K** |

Class-to-domain mapping is config-driven via `domains.yaml`:

```yaml
core: [Application, Document, Base, "*Input", "Point*", "Vector*", "Matrix*", ObjectCollection]
sketch: ["Sketch*", "*Constraint", "*Dimension", "Profile*"]
features: ["*Feature", "*Features", "*FeatureInput"]
bodies: ["BRep*", "Mesh*", "TSpline*"]
assembly: [Component, Occurrence, "*Joint*", RigidGroup]
cam: ["CAM*", Operation, Toolpath, Tool, "*Post*", NCProgram]
drawing: ["Drawing*", "*Annotation*", "*Table"]
ui: [Command, "*CommandInput*", Palette, Toolbar, "*Event*", UserInterface]
```

Unmatched classes go to `fusion-misc.lap`.

## Converter Architecture

Python CLI package at `fusion_lap/`.

### Pipeline

```
Stage 1: Discover & Parse Stubs
  discover.py tries in order:
    1. pip import fusionscript-stubs
    2. pip import adsk
    3. Auto-discover Fusion install (platform-aware glob)
    4. Fall back to skeleton from HTML docs alone
  stubs.py parses .pyi into intermediate representation (IR)

Stage 2: Scrape & Enrich
  scraper.py fetches Autodesk CloudHelp HTML:
    - Starts from reference manual index
    - Follows links to each class page
    - Extracts descriptions, method docs, code samples
    - Caches HTML locally (skip re-fetch unless --refresh)
  enrich.py merges scraped data into IR

Stage 3: Classify & Render
  domains.yaml maps classes to domain files
  render.py walks IR per domain and emits .lap format:
    - [types] for enums and value types
    - [classes] with inheritance, properties, methods
    - Top ~50 classes: inherited members inlined
    - [examples] from scraped code samples
    - [gotchas] from hand-maintained config

Stage 4: Bundle
  Concatenate graph + gotchas + core -> fusion-base.lap
  Log token counts per file (tiktoken)
  Print summary table
```

### Intermediate Representation

```python
IR = {
  "adsk.core": {
    "Point3D": {
      "parent": "Base",
      "description": "A 3D point.",
      "properties": {
        "x": {"type": "float", "description": "The x coordinate."},
        ...
      },
      "methods": {
        "create": {
          "args": [{"name": "x", "type": "float"}, ...],
          "returns": "Point3D",
          "static": True,
          "description": "Creates a Point3D."
        }
      }
    }
  },
  "adsk.fusion": { ... },
  "adsk.cam": { ... }
}
```

### Fusion Install Auto-Discovery

`discover.py` searches platform-specific paths automatically:

```
macOS:
  ~/Library/Application Support/Autodesk/webdeploy/production/*/Autodesk Fusion.app/
  /Applications/Autodesk Fusion.app/

Windows:
  %LOCALAPPDATA%/Autodesk/webdeploy/production/*/

Linux:
  ~/.local/share/autodesk/webdeploy/production/*/
```

Within those, stubs live under `Api/Python/packages/adsk/`. Picks the most recent
version if multiple exist. Env var `FUSION_PATH` as escape hatch, never required.

### CLI

```bash
# Full build (stubs + HTML enrichment)
python -m fusion_lap build --output lap/

# Stubs only (offline, no descriptions)
python -m fusion_lap build --output lap/ --no-enrich

# Rebuild single domain
python -m fusion_lap build --output lap/ --domain sketch

# Force re-fetch HTML (ignore cache)
python -m fusion_lap build --output lap/ --refresh
```

## Delivery Mechanisms

| Mechanism | Audience | Setup |
|---|---|---|
| **CLAUDE.md includes** | Claude Code users who clone the repo | Zero setup |
| **MCP server** | Claude Code / MCP-capable tools | `pip install`, add to MCP config |
| **Copy-paste fusion-base.lap** | Any LLM, any tool | Manual, universal |
| **Internal raw URLs** | Internal LLM tools with git.autodesk.com access | Tool-dependent |

### CLAUDE.md

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

### MCP Server

Thin Python wrapper (~100 lines) in `fusion_lap/mcp_server.py`:

```
Tools:
  fusion_api_lookup(domain: str) -> str    # Returns full .lap file content
  fusion_api_search(query: str) -> str     # Searches across all .lap files
  fusion_api_graph() -> str                # Returns fusion-graph.lap
```

Configured in Claude Code MCP settings or run standalone.

## Repo Structure

```
fusion-lap-sdk/
  docs/
    lap-research.md
    fusion-research.md
    fusion-lap-design.md
  fusion_lap/
    __main__.py
    discover.py
    stubs.py
    scraper.py
    enrich.py
    render.py
    mcp_server.py
  domains.yaml
  lap/
    fusion-base.lap
    fusion-graph.lap
    fusion-gotchas.lap
    fusion-core.lap
    fusion-sketch.lap
    fusion-features.lap
    fusion-bodies.lap
    fusion-assembly.lap
    fusion-cam.lap
    fusion-drawing.lap
    fusion-ui.lap
    fusion-misc.lap
  CLAUDE.md
  pyproject.toml
  README.md
```

## Open Questions

1. **Top-50 classes** -- which classes get inherited members inlined? Needs profiling
   of real Fusion scripts to determine most-used classes.
2. **Hand-maintained gotchas** -- the `[gotchas]` section can't be auto-generated.
   Needs curation from Fusion API experience.
3. **Example quality** -- scraped examples from CloudHelp may be verbose or incomplete.
   May need hand-curation for the most common patterns.
4. **Token budget accuracy** -- estimates are rough until we run the converter on real
   data. Actual counts may shift domain boundaries.
