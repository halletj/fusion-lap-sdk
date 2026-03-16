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

    _print_summary(out)


def _load_domains(domains_yaml: str) -> dict[str, list[str]]:
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
