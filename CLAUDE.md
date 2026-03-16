# Autodesk Fusion API Reference

Compressed API reference for the Autodesk Fusion SDK in .lap format.

## Always read before writing Autodesk Fusion scripts:
- lap/fusion-base.lap (navigation graph, gotchas, core types — ~20K tokens)

## Load the relevant domain file when needed:
- lap/fusion-sketch.lap — sketches, curves, constraints, profiles
- lap/fusion-features.lap — extrude, revolve, loft, sweep, fillet, etc.
- lap/fusion-bodies.lap — BRep, mesh, T-spline geometry
- lap/fusion-assembly.lap — components, joints, occurrences
- lap/fusion-cam.lap — CAM setup, toolpaths, operations
- lap/fusion-drawing.lap — drawing views, dimensions, annotations
- lap/fusion-ui.lap — commands, palettes, toolbars, events
- lap/fusion-misc.lap — enums, settings types, and other uncategorized classes

## If files are not local, fetch from:
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-base.lap
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-sketch.lap
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-features.lap
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-bodies.lap
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-assembly.lap
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-cam.lap
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-drawing.lap
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-ui.lap
- https://halletj.github.io/fusion-lap-sdk/lap/fusion-misc.lap

## When writing Autodesk Fusion scripts:
- Always import: import adsk.core, adsk.fusion, adsk.cam
- Units are centimeters internally
- Check return values for None
- Use the [graph] section in fusion-base.lap to navigate the object model
