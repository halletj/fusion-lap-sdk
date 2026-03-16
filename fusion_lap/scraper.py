"""Parse Fusion API HTML documentation from a local clone of FusionAPIReference."""

import logging
import re
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

from .ir import ClassDef, MethodDef, PropertyDef

logger = logging.getLogger(__name__)

_REPO_URL = "https://github.com/AutodeskFusion360/FusionAPIReference.git"
_CLONE_DIR = Path.home() / ".cache" / "fusion-lap" / "FusionAPIReference"
_DOCS_SUBDIR = "Fusion_API_Documentation" / Path("files")


def find_or_clone_docs() -> Path | None:
    """Find local FusionAPIReference docs, cloning the repo if needed."""
    # Check common locations
    candidates = [
        _CLONE_DIR / _DOCS_SUBDIR,
        Path("/tmp/FusionAPIReference") / _DOCS_SUBDIR,
        Path.home() / "git" / "FusionAPIReference" / _DOCS_SUBDIR,
    ]
    for candidate in candidates:
        if candidate.is_dir() and any(candidate.glob("*.htm")):
            return candidate

    # Not found -- clone it
    logger.info(f"Cloning {_REPO_URL} to {_CLONE_DIR}...")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", _REPO_URL, str(_CLONE_DIR)],
            check=True,
            capture_output=True,
            text=True,
        )
        docs_dir = _CLONE_DIR / _DOCS_SUBDIR
        if docs_dir.is_dir():
            return docs_dir
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Failed to clone FusionAPIReference: {e}")

    return None


def parse_class_page(class_name: str, html: str) -> ClassDef:
    """Parse a single class HTML page into a ClassDef."""
    soup = BeautifulSoup(html, "html.parser")

    # Extract parent -- may be in a <p> tag or loose text after <h1>
    parent = ""
    body = soup.find("body")
    if body:
        body_text = body.get_text()
        match = re.search(r"Derived from:\s*(\w+)", body_text)
        if match:
            parent = match.group(1)
        # Also try finding it via link next to "Derived from"
        for a_tag in soup.find_all("a"):
            prev = a_tag.previous_sibling
            if prev and isinstance(prev, NavigableString) and "Derived from:" in str(prev):
                parent = a_tag.get_text().strip()
                break

    # Extract description -- text after <h2>Description</h2>
    description = ""
    for h2 in soup.find_all("h2"):
        if "description" in h2.get_text().strip().lower():
            # Get text between this h2 and the next h2
            parts = []
            for sibling in h2.next_siblings:
                if sibling.name == "h2":
                    break
                text = sibling.get_text().strip() if hasattr(sibling, "get_text") else str(sibling).strip()
                if text:
                    parts.append(text)
            description = " ".join(parts)
            break

    # Fallback: try <p> tags
    if not description:
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if text and "Derived from:" not in text and "Defined in" not in text:
                description = text
                break

    # Extract methods and properties from tables following h2 headers
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


def scrape_local_docs(docs_dir: Path | None = None) -> dict[str, ClassDef]:
    """Parse all class HTML pages from a local FusionAPIReference clone."""
    if docs_dir is None:
        docs_dir = find_or_clone_docs()
    if docs_dir is None:
        return {}

    logger.info(f"Reading HTML docs from {docs_dir}")

    # Class pages are ClassName.htm (no underscore -- underscore means method/property page)
    class_files = sorted(
        f for f in docs_dir.glob("*.htm")
        if "_" not in f.stem and f.stem[0].isupper()
    )

    scraped = {}
    for class_file in class_files:
        class_name = class_file.stem
        try:
            html = class_file.read_text(encoding="utf-8")
            scraped[class_name] = parse_class_page(class_name, html)
        except Exception as e:
            logger.debug(f"Failed to parse {class_file.name}: {e}")

    logger.info(f"Parsed {len(scraped)} class pages from local docs")
    return scraped
