"""Scrape Autodesk CloudHelp HTML for Fusion API class documentation."""

import logging
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from .ir import ClassDef, MethodDef, PropertyDef

logger = logging.getLogger(__name__)

BASE_URL = "https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files"
CACHE_DIR = Path.home() / ".cache" / "fusion-lap" / "html"


def parse_class_page(class_name: str, html: str) -> ClassDef:
    """Parse a single class HTML page into a ClassDef (descriptions only, no types)."""
    soup = BeautifulSoup(html, "html.parser")

    parent = ""
    for p in soup.find_all("p"):
        text = p.get_text()
        if "Derived from:" in text:
            link = p.find("a")
            if link:
                parent = link.get_text().strip()
            break

    description = ""
    for p in soup.find_all("p"):
        text = p.get_text().strip()
        if text and "Derived from:" not in text and "Defined in" not in text:
            description = text
            break

    methods = {}
    properties = {}
    current_section = ""

    for element in soup.find_all(["h2", "table"]):
        if element.name == "h2":
            current_section = element.get_text().strip().lower()
        elif element.name == "table":
            for row in element.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    name_cell = cells[0]
                    desc_cell = cells[1]
                    link = name_cell.find("a")
                    name = link.get_text().strip() if link else name_cell.get_text().strip()
                    desc = desc_cell.get_text().strip()

                    if "method" in current_section:
                        methods[name] = MethodDef(name=name, description=desc)
                    elif "propert" in current_section:
                        read_only = "Gets and sets" not in desc
                        properties[name] = PropertyDef(name=name, description=desc, read_only=read_only)

    return ClassDef(
        name=class_name, parent=parent, description=description,
        methods=methods, properties=properties,
    )


def fetch_class_page(class_name: str, refresh: bool = False) -> str | None:
    """Fetch a class page from CloudHelp, with local caching."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{class_name}.htm"

    if cache_file.exists() and not refresh:
        return cache_file.read_text(encoding="utf-8")

    url = f"{BASE_URL}/{class_name}.htm"
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30)
        if resp.status_code == 200:
            html = resp.text
            cache_file.write_text(html, encoding="utf-8")
            return html
        else:
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return None
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def scrape_class_index(refresh: bool = False) -> list[str]:
    """Fetch the reference manual index and extract all class names."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "_index.htm"

    if cache_file.exists() and not refresh:
        html = cache_file.read_text(encoding="utf-8")
    else:
        url = f"{BASE_URL}/ReferenceManual_UM.htm"
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=30)
            html = resp.text
            cache_file.write_text(html, encoding="utf-8")
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch index: {e}")
            return []

    soup = BeautifulSoup(html, "html.parser")
    class_names = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]
        match = re.match(r"^([A-Z][A-Za-z0-9]+)\.htm$", href)
        if match:
            class_names.add(match.group(1))

    return sorted(class_names)
