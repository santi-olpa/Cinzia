import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"

_cache: dict[str, str] = {}


def load_fleet_knowledge(fleet: str) -> str:
    """
    Load knowledge base content for a given fleet.
    fleet: 'argentina' | 'miami' | 'unknown'
    Returns the full text content to inject into the system prompt.
    """
    if fleet in _cache:
        return _cache[fleet]

    fleet_dir = KB_DIR / fleet
    if not fleet_dir.exists():
        logger.warning(f"Knowledge base directory not found: {fleet_dir}")
        return ""

    parts = []
    for file in sorted(fleet_dir.iterdir()):
        if file.suffix in (".txt", ".md"):
            try:
                content = file.read_text(encoding="utf-8")
                parts.append(f"### {file.stem}\n{content}")
                logger.info(f"Loaded KB file: {file.name} ({len(content)} chars)")
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")

    combined = "\n\n".join(parts)
    _cache[fleet] = combined
    return combined


def get_knowledge_section(fleet: str) -> str:
    """Return the KB section ready to include in system prompt."""
    content = load_fleet_knowledge(fleet)
    if not content:
        return ""
    fleet_label = "Argentina (Cinzia Sprinter)" if fleet == "argentina" else "Miami (Entegra Odyssey SE)"
    return f"## Manual técnico — Flota {fleet_label}\n\n{content}"


def reload_cache():
    """Force reload of all cached KB content (useful after updating manuals)."""
    _cache.clear()
    logger.info("Knowledge base cache cleared")
