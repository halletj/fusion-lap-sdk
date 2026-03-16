"""CLI entry point for fusion-lap converter."""

import logging

from .build import build_lap_files

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    """Build .lap files from Fusion API stubs + docs."""
    build_lap_files()


if __name__ == "__main__":
    main()
