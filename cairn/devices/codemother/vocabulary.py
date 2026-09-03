"""codemother/vocabulary.py — universal pattern vocabulary, project-agnostic.

GOF/SOLID/architectural smells seeded as typed entries. Lives at the device
level (not per-project) because these patterns apply to any codebase.
The catalog is loaded from vocabulary_catalog.json beside this file.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.devices.codemother.types import PatternType, PatternSignal, TypePolarity

_CATALOG_PATH = Path(__file__).parent / "vocabulary_catalog.json"


def load_catalog() -> list[PatternType]:
    """Load the universal vocabulary catalog."""
    if not _CATALOG_PATH.exists():
        return []
    entries = json.loads(_CATALOG_PATH.read_text())
    return [PatternType.from_dict(e) for e in entries]


def catalog_names() -> list[str]:
    """Return the names in the catalog without loading full entries."""
    if not _CATALOG_PATH.exists():
        return []
    entries = json.loads(_CATALOG_PATH.read_text())
    return [e["name"] for e in entries]
