"""Auto-discover Fusion API type stubs from multiple sources."""

import importlib.util
import logging
import os
import platform
from dataclasses import dataclass
from glob import glob
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StubSource:
    path: str
    kind: str  # "pip_fusionscript", "pip_adsk", "fusion_install", "fusion_env"


def find_stubs() -> StubSource | None:
    """Try multiple sources to find Fusion API stubs. Returns first success or None."""
    finders = [
        _try_fusion_env,
        _try_pip_fusionscript_stubs,
        _try_pip_adsk,
        _try_fusion_install,
    ]
    for finder in finders:
        try:
            result = finder()
            if result:
                logger.info(f"Found stubs: {result.kind} at {result.path}")
                return result
        except Exception as e:
            logger.debug(f"{finder.__name__} failed: {e}")
    logger.warning("No stub source found. Will rely on HTML scraping alone.")
    return None


def _try_fusion_env() -> StubSource | None:
    fusion_path = os.environ.get("FUSION_PATH")
    if not fusion_path:
        return None
    candidates = [
        Path(fusion_path) / "Api" / "Python" / "packages" / "adsk",
        Path(fusion_path) / "adsk",
    ]
    for candidate in candidates:
        if candidate.is_dir() and _has_stubs(candidate):
            return StubSource(path=str(candidate), kind="fusion_env")
    return None


def _try_pip_fusionscript_stubs() -> StubSource | None:
    spec = importlib.util.find_spec("adsk")
    if spec and spec.origin:
        path = Path(spec.origin).parent
        if _has_stubs(path):
            return StubSource(path=str(path), kind="pip_fusionscript")
    return None


def _try_pip_adsk() -> StubSource | None:
    spec = importlib.util.find_spec("adsk")
    if spec and spec.submodule_search_locations:
        for loc in spec.submodule_search_locations:
            path = Path(loc)
            if path.is_dir():
                return StubSource(path=str(path), kind="pip_adsk")
    return None


def _try_fusion_install() -> StubSource | None:
    system = platform.system()
    home = Path.home()
    if system == "Darwin":
        patterns = [
            str(home / "Library/Application Support/Autodesk/webdeploy/production/*/Autodesk Fusion.app/Contents/Api/Python/packages/adsk"),
            "/Applications/Autodesk Fusion.app/Contents/Api/Python/packages/adsk",
            str(home / "Library/Application Support/Autodesk/webdeploy/production/*/Api/Python/packages/adsk"),
        ]
    elif system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", str(home / "AppData/Local"))
        patterns = [f"{local_app_data}/Autodesk/webdeploy/production/*/Api/Python/packages/adsk"]
    elif system == "Linux":
        patterns = [str(home / ".local/share/autodesk/webdeploy/production/*/Api/Python/packages/adsk")]
    else:
        return None
    all_matches = []
    for pattern in patterns:
        all_matches.extend(glob(pattern))
    if not all_matches:
        return None
    all_matches.sort(key=lambda p: Path(p).stat().st_mtime, reverse=True)
    return StubSource(path=all_matches[0], kind="fusion_install")


def _has_stubs(path: Path) -> bool:
    return any(
        (path / f).exists()
        for f in ("__init__.pyi", "__init__.py", "core.pyi", "fusion.pyi")
    )
