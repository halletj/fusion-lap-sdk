# fusion-lap

Compressed, LLM-optimized API reference for the Autodesk Fusion SDK.

Fusion LAP generates `.lap` files — compact API reference documents designed to fit
in an LLM context window — from the Fusion 360 Python API stubs and online
documentation.

## Installation

```bash
pip install -e .
```

## Usage

```bash
fusion-lap build              # build all .lap files to lap/
fusion-lap build -o out/      # custom output directory
fusion-lap build --domain cam # rebuild a single domain
fusion-lap build --refresh    # force re-fetch HTML docs
fusion-lap build --no-enrich  # stubs only, skip HTML enrichment
```

## Project structure

```
fusion_lap/         Python package
  __main__.py       CLI (click)
  ir.py             Intermediate representation data model
domains.yaml        Maps Fusion API classes to domain .lap files
lap/                Generated .lap output (not checked in)
tests/              Test suite
```

## Development

```bash
python -m pytest
```

## How it works

1. Parse Fusion API Python stubs into an intermediate representation (IR).
2. Optionally enrich the IR with descriptions scraped from the online docs.
3. Partition classes into domain files using patterns in `domains.yaml`.
4. Emit `.lap` files compact enough for LLM context windows.
