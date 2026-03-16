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
