# Can LAPIS Be Applied to the Autodesk Fusion API?

Research into adapting LAPIS (Lightweight API Specification for Intelligent Systems) --
a token-efficient API description format designed for REST APIs -- to the Autodesk
Fusion desktop SDK.

## The Autodesk Fusion API

### Overview

The Fusion API is an **object-oriented** SDK for automating Autodesk Fusion (formerly
Fusion 360) through Python or C++ scripts and add-ins. It is **not** a REST API -- it
is a local, in-process desktop SDK where scripts run inside the Fusion application.

### Architecture

- **Top-level object:** `Application` -- represents the running Fusion instance
- **Hierarchy:** Application > Documents > Design > Root Component > child objects
  (Sketches, Features, Bodies, Components, etc.)
- **Namespaces:** `adsk.core` (shared foundation), `adsk.fusion` (design/modeling),
  `adsk.cam` (manufacturing)
- **Pattern:** Strongly-typed OOP with collections, input objects, events, and
  inheritance hierarchies

### Scale of the API

The Fusion API is **massive**:

- Three namespaces (`adsk.core`, `adsk.fusion`, `adsk.cam`)
- Estimated **500+ classes** spanning parametric modeling, sketching, features
  (extrude, revolve, loft, sweep, etc.), assembly/joints, mesh, construction geometry,
  CAM toolpaths, drawing/annotations, and more
- Each class exposes multiple **properties**, **methods**, and **events**
- Deep inheritance trees (e.g., `Base` > `Feature` > `ExtrudeFeature`)
- **Collections** with `count`, `item()`, `add()`, iteration
- **Input objects** that act as parameter builders (analogous to command dialogs)

A full API reference -- even as Python type stubs -- likely runs into **hundreds of
thousands of tokens**, making it far too large for any LLM context window.

### Current Approaches: Fusion + LLMs

Two existing MCP (Model Context Protocol) servers address the Fusion API + LLM
challenge:

1. **[Fusion 360 MCP Server](https://github.com/AuraFriday/Fusion-360-MCP-Server)**
   by AuraFriday -- enables AI agents to control Fusion via MCP. Uses three
   documentation strategies:
   - **Runtime introspection** -- search by class name at runtime
   - **Online doc fetching** -- pulls from Autodesk's CloudHelp with parameter tables
     and code samples
   - **Best practices guide** -- built-in patterns for coordinate systems, naming, etc.

2. **[fusion-360-mcp-server](https://lobehub.com/mcp/luiscarone-fusion-360-mcp-server)**
   by luiscarone -- indexes Fusion API docs into `fusion_api_index.json` for LLM
   querying, code generation, and API reference lookup.

Both use **on-demand retrieval** rather than stuffing the entire API into context --
a key insight for any LAPIS adaptation.

## LAPIS: What It Was Designed For

LAPIS targets **REST/HTTP APIs** described by OpenAPI specifications:

- Operations are HTTP methods on URL paths (`POST /invoices`)
- Input/output are JSON request/response bodies
- Errors are HTTP status codes
- Rate limits apply to HTTP endpoints
- Flows describe sequences of HTTP calls

Its seven sections (`[meta]`, `[types]`, `[ops]`, `[webhooks]`, `[errors]`, `[limits]`,
`[flows]`) directly model REST concepts.

## Gap Analysis: REST API vs Desktop OOP SDK

| Concept | REST API (LAPIS) | Desktop SDK (Fusion) |
|---|---|---|
| **Operations** | HTTP verb + path | Methods on object instances |
| **Inputs** | JSON body, query params, headers | Method arguments, input objects |
| **Outputs** | JSON response body | Return values, mutated state |
| **Types** | Flat DTOs | Deep class hierarchies with inheritance |
| **State** | Stateless requests | Stateful object graph in memory |
| **Errors** | HTTP status codes | Exceptions, return codes |
| **Discovery** | Single base URL | Navigate object graph from `Application` root |
| **Side effects** | Isolated per-request | Methods mutate document state |
| **Collections** | Paginated list endpoints | In-memory collections with iteration |
| **Events** | Webhooks | Event handlers/callbacks |
| **Relationships** | Hyperlinks / IDs | Object references, parent-child hierarchy |

### Key Gaps

1. **No inheritance model** -- LAPIS types are flat structures (like JSON Schema
   objects). Fusion relies heavily on inheritance (`Feature` > `ExtrudeFeature`,
   `SketchEntity` > `SketchLine`).

2. **No concept of methods on objects** -- LAPIS operations are standalone endpoints.
   Fusion methods belong to specific classes (`Component.bRepBodies`,
   `Sketches.add()`).

3. **No object graph navigation** -- REST APIs have flat URL namespaces. Fusion
   requires traversing `app.activeDocument.design.rootComponent.features.extrudeFeatures`.

4. **No state/context** -- LAPIS assumes stateless request-response. Fusion scripts
   operate on a live document with persistent state.

5. **No events** -- LAPIS has webhooks (external push). Fusion has event handlers that
   fire within the application process.

6. **Scale mismatch** -- LAPIS benchmarks show 800-313K tokens for complete API specs.
   The Fusion API would likely exceed 500K tokens even in a compressed format,
   making "whole API in context" impractical.

## Can LAPIS Be Adapted? A Feasibility Assessment

### What Transfers Well

Some LAPIS principles apply directly:

- **`[meta]` section** -- API name, version, language, authentication/setup
- **`[types]` section** -- Type definitions with minor extensions for inheritance
- **`[flows]` section** -- Multi-step operation sequences map well to Fusion scripting
  patterns (create sketch > add geometry > create feature > boolean)
- **Signature-based syntax** -- Compact method signatures work for any callable
- **Token minimality philosophy** -- The core insight (structural compression > format
  compression) is universal

### What Needs Reinvention

A "LAPIS for SDKs" would need fundamentally new sections and concepts:

#### 1. Class Hierarchy Section `[classes]`

```
[classes]

# Inheritance with ":" syntax
Feature : Base
  name: str
  isValid: bool
  timelineObject: TimelineObject
  deleteMe() -> bool

ExtrudeFeature : Feature
  extentOne: ExtentDefinition
  operation: FeatureOperations
  startExtent: ExtentDefinition
  setOneSideExtent(extent: ExtentDefinition, direction: ExtentDirections) -> bool
```

#### 2. Object Graph Navigation `[graph]`

```
[graph]
Application
  .activeDocument -> Document
    .design -> Design
      .rootComponent -> Component
        .sketches -> Sketches *collection
          .add(planarEntity) -> Sketch
        .features -> Features
          .extrudeFeatures -> ExtrudeFeatures *collection
            .addSimple(profile, distance, operation) -> ExtrudeFeature
```

#### 3. Collections Pattern

```
[collections]
# Generic collection pattern -- applies to all *Collection types
*Collection<T>:
  count: int
  item(index: int) -> T
  [index] -> T  # Python subscript
  __iter__ -> T  # Python iteration
```

#### 4. Events Section `[events]`

```
[events]
CommandCreatedEventHandler
  ! When a command is created in the UI
  > args: CommandCreatedEventArgs
    .command -> Command
    .command.commandInputs -> CommandInputs
```

#### 5. Scoped Operations (Methods-on-Classes)

Replace standalone `[ops]` with class-scoped methods:

```
Sketch:
  .sketchCurves -> SketchCurves
  .sketchPoints -> SketchPoints
  .profiles -> Profiles
  .isVisible: bool

SketchLines : SketchCurves
  addByTwoPoints(start: Point3D, end: Point3D) -> SketchLine
  addCenterPointRectangle(center: Point3D, corner: Point3D) -> ObjectCollection
```

### Estimated Compression Potential

Applying LAPIS-style compression to a desktop SDK could achieve significant savings,
though likely less than the 85% seen with REST APIs:

| Savings Source | Estimated | Notes |
|---|---|---|
| Metadata elimination | ~20% | Remove descriptions, examples, see-also links |
| Signature syntax vs verbose docs | ~30% | One-line methods vs multi-paragraph HTML docs |
| Inheritance flattening | ~10% | Show only new members, reference parent |
| Pattern deduplication | ~10% | Collection, Input Object, Event patterns declared once |
| **Total estimated reduction** | **~60-70%** | Less than REST (85%) due to inherent OOP complexity |

For the Fusion API, this could mean reducing from ~500K+ tokens (full docs) to
~150-200K tokens -- still too large for a single context load, but far more manageable
for **chunked retrieval**.

## Recommended Architecture: Hybrid Approach

Given the scale of the Fusion API, a pure "load everything into context" approach
(LAPIS's original use case) won't work. Instead, a hybrid architecture is recommended:

### 1. LAPIS-Inspired Compact Format (the "Fusion LAP" format)

Create a compressed representation of the entire Fusion API using adapted LAPIS
principles:

```
[meta]
api: Autodesk Fusion
version: 2.0
lang: python
namespace: adsk.core, adsk.fusion, adsk.cam
import: import adsk.core, adsk.fusion, adsk.cam

[types]
Point3D: x:float, y:float, z:float
Vector3D: x:float, y:float, z:float
Matrix3D: ...
ValueInput:
  .createByReal(real: float) -> ValueInput @static
  .createByString(expression: str) -> ValueInput @static

FeatureOperations: join | cut | intersect | new_body

[classes]
Application : Base
  .activeDocument -> Document
  .userInterface -> UserInterface
  ...

[graph]
Application -> Document -> Design -> Component -> Features
                                                -> Sketches
                                                -> BRepBodies
                                  -> Component[] (children)

[flows]
basic_extrude "Create a simple extruded box"
  get_design -> get_root_component -> create_sketch
  -> add_rectangle -> get_profile -> create_extrude
```

### 2. Tiered Retrieval Strategy

| Tier | Content | When to Load |
|---|---|---|
| **Always in context** | `[meta]`, `[graph]`, `[flows]`, core `[types]` (~5-10K tokens) | Every conversation |
| **On-demand summary** | Class signatures for relevant domain (~10-30K tokens) | When user mentions a domain (sketching, CAM, etc.) |
| **On-demand detail** | Full class with all methods/properties | When user needs specific class reference |
| **Examples** | Code samples for specific patterns | When user asks "how do I..." |

### 3. Domain Partitioning

Split the Fusion API into independently-loadable domain files:

```
fusion-core.lap        # Application, Document, base types (~3K tokens)
fusion-sketch.lap      # Sketch, SketchCurves, Constraints (~15K tokens)
fusion-features.lap    # Extrude, Revolve, Loft, Sweep, etc. (~20K tokens)
fusion-bodies.lap      # BRep, Mesh, T-Spline geometry (~10K tokens)
fusion-assembly.lap    # Components, Joints, Motion (~10K tokens)
fusion-cam.lap         # CAM setup, toolpaths, operations (~15K tokens)
fusion-drawing.lap     # Drawing views, dimensions, annotations (~8K tokens)
fusion-ui.lap          # Commands, Palettes, UI elements (~5K tokens)
```

Total: ~86K tokens for the full API in compressed form -- a **~80% reduction** from
raw documentation while being **partitioned for selective loading**.

## Comparison of Approaches

| Approach | Tokens in Context | API Coverage | LLM Accuracy |
|---|---|---|---|
| Full OpenAPI-style docs | 500K+ (won't fit) | 100% | N/A |
| MCP runtime introspection | ~2-5K per query | Per-query | Good for known classes |
| MCP doc fetching | ~5-10K per query | Per-query | Good with examples |
| **Fusion LAP (proposed)** | **5-30K selective** | **Domain-scoped** | **Best: structured + navigable** |
| Fusion LAP + MCP hybrid | 5-30K + on-demand | Full | Best overall |

## Conclusions

### LAPIS Can Be Adapted, But Needs Extension

LAPIS as-is is a REST API format and cannot directly describe the Fusion API. However,
its **core philosophy** (structural compression, signature syntax, deduplication,
token minimality) is highly applicable. A "LAPIS for SDKs" extension would need:

1. Class inheritance syntax
2. Object graph navigation
3. Method-on-class scoping
4. Collection/pattern templates
5. Event handler descriptions

### The Real Win: Structured Compression + Selective Loading

The biggest insight from this research is that the value isn't in fitting the whole API
into context (impossible for Fusion's scale), but in having a **structured, compressed
format** that enables:

- **Intelligent chunking** -- load only relevant domains
- **Hierarchical navigation** -- always-on graph helps LLMs find the right classes
- **Pattern deduplication** -- declare collection/input/event patterns once
- **Flow documentation** -- multi-step recipes for common tasks

### Recommended Next Steps

1. **Define a "LAP for SDKs" spec** extending LAPIS with OOP constructs
2. **Build a scraper/converter** for Autodesk's Fusion API reference docs
3. **Partition into domain files** following the tiered strategy above
4. **Benchmark** token counts and LLM accuracy vs raw docs and MCP approaches
5. **Consider MCP integration** -- serve LAP files through an MCP server for the best
   of both worlds

## Sources

- [LAPIS Paper (arXiv)](https://arxiv.org/abs/2602.18541)
- [LAPIS GitHub Repository](https://github.com/cr0hn/LAPIS)
- [Fusion API Getting Started](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BasicConcepts_UM.htm)
- [Fusion API Reference Manual](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ReferenceManual_UM.htm)
- [Fusion API Overview](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-A92A4B10-3781-4925-94C6-47DA85A4F65A)
- [Autodesk Platform Services - Fusion API](https://aps.autodesk.com/developer/overview/autodesk-fusion-api)
- [Fusion 360 MCP Server (AuraFriday)](https://github.com/AuraFriday/Fusion-360-MCP-Server)
- [Fusion 360 MCP Server (luiscarone)](https://lobehub.com/mcp/luiscarone-fusion-360-mcp-server)
- [TOON Format](https://github.com/toon-format/toon)
