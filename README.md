# Fusion LAP SDK

Compressed, LLM-optimized API reference for the Autodesk Fusion SDK.

**114K tokens** covering 1,553 classes — the entire Fusion API in a format any LLM can use.

## Use with any LLM

Paste this into any LLM prompt (ChatGPT, Claude, Gemini, etc.):

```
Read https://halletj.github.io/fusion-lap-sdk/lap/fusion-base.lap for the Fusion API reference.
For additional API domains see https://halletj.github.io/fusion-lap-sdk/CLAUDE.md
Help me write a Fusion script that [your task here].
```

## Use with Claude Code

Clone this repo. The `CLAUDE.md` file tells Claude Code where to find the API reference automatically.

```bash
git clone https://github.com/halletj/fusion-lap-sdk.git
cd fusion-lap-sdk
# Claude Code reads CLAUDE.md and knows how to use the .lap files
```

## LAP Files

Pre-built `.lap` files are in the `lap/` directory, hosted at `https://halletj.github.io/fusion-lap-sdk/lap/`:

| File | Tokens | Contents |
|---|---|---|
| [fusion-base.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-base.lap) | ~20K | **Start here.** Navigation graph + gotchas + core types |
| [fusion-features.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-features.lap) | ~26K | Extrude, Revolve, Loft, Sweep, Fillet, Chamfer, etc. |
| [fusion-core.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-core.lap) | ~20K | Application, Point3D, Vector3D, ValueInput, etc. |
| [fusion-sketch.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-sketch.lap) | ~14K | Sketch, SketchCurves, Constraints, Profiles |
| [fusion-bodies.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-bodies.lap) | ~10K | BRepBody, BRepFace, MeshBody, etc. |
| [fusion-ui.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-ui.lap) | ~10K | Command, CommandInputs, Toolbar, Events |
| [fusion-cam.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-cam.lap) | ~7K | CAM setup, toolpaths, operations |
| [fusion-assembly.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-assembly.lap) | ~6K | Component, Occurrence, Joint |
| [fusion-drawing.lap](https://halletj.github.io/fusion-lap-sdk/lap/fusion-drawing.lap) | ~1K | Drawing views, dimensions, annotations |

## Regenerating

If you have Fusion installed, you can regenerate the `.lap` files from your local API stubs:

```bash
pip install -e .
python -m fusion_lap
```

The tool automatically:
1. Finds Fusion API stubs from your local install
2. Clones [FusionAPIReference](https://github.com/AutodeskFusion360/FusionAPIReference) for HTML descriptions
3. Merges stubs (types/signatures) + HTML (descriptions)
4. Renders partitioned `.lap` files to `lap/`

## What is LAP?

LAP is a compressed API reference format inspired by [LAPIS](https://arxiv.org/abs/2602.18541), extended for object-oriented desktop SDKs. It uses compact syntax — class inheritance with `:`, properties without parens, methods with parens, `*collection<T>` shorthand — to fit large API surfaces into LLM context windows.

See [docs/lap-research.md](docs/lap-research.md) and [docs/fusion-research.md](docs/fusion-research.md) for the full research.

## Project Structure

```
lap/                Generated .lap files (checked in, ready to use)
fusion_lap/         Python converter package
  __main__.py       Entry point: python -m fusion_lap
  ir.py             Intermediate representation
  discover.py       Auto-find Fusion stubs
  stubs.py          Parse .py/.pyi stubs into IR
  scraper.py        Parse FusionAPIReference HTML docs
  enrich.py         Merge stubs + HTML descriptions
  render.py         IR -> .lap format
  mcp_server.py     MCP tool functions
domains.yaml        Class-to-domain mapping
tests/              Test suite (36 tests)
docs/               Research and design docs
```
