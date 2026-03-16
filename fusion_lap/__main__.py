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
