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
