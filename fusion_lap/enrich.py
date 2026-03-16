"""Enrich stub-derived IR with descriptions from scraped HTML."""

import logging

from .ir import IR, ClassDef

logger = logging.getLogger(__name__)


def enrich_ir(ir: IR, scraped: dict[str, ClassDef]):
    """Merge scraped class data into the existing IR."""
    for class_name, scraped_cls in scraped.items():
        found = False
        for ns_classes in ir.namespaces.values():
            if class_name in ns_classes:
                existing = ns_classes[class_name]
                scraped_cls.namespace = existing.namespace
                ir.merge_class(scraped_cls)
                found = True
                break

        if not found:
            if not scraped_cls.namespace:
                scraped_cls.namespace = _guess_namespace(class_name)
            ir.add_class(scraped_cls)
            logger.info(f"Added {class_name} from HTML (not in stubs)")


def _guess_namespace(class_name: str) -> str:
    fusion_prefixes = (
        "Sketch", "Feature", "BRep", "Mesh", "TSpline", "Component",
        "Occurrence", "Joint", "Extrude", "Revolve", "Loft", "Sweep",
        "Fillet", "Chamfer", "Shell", "Hole", "Thread", "Pattern",
        "Design", "Timeline", "Profile",
    )
    cam_prefixes = ("CAM", "Setup", "Operation", "Toolpath", "Tool", "NC", "Post")

    for prefix in cam_prefixes:
        if class_name.startswith(prefix):
            return "adsk.cam"
    for prefix in fusion_prefixes:
        if class_name.startswith(prefix):
            return "adsk.fusion"
    return "adsk.core"
