"""Persistent topic registry.

Stores topics in a local JSON file so uploaded materials automatically
become selectable topics that survive restarts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_TOPICS_FILE = _DATA_DIR / "topics.json"

DEFAULT_TOPICS = [
    "Recursion",
    "Sorting Algorithms",
    "Binary Trees",
    "Graph Traversal",
    "Dynamic Programming",
]


def _ensure_file() -> Path:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _TOPICS_FILE.exists():
        _TOPICS_FILE.write_text(json.dumps(DEFAULT_TOPICS, indent=2), encoding="utf-8")
    return _TOPICS_FILE


def load_topics() -> list[str]:
    """Load all topics (defaults + user-added), deduplicated."""
    path = _ensure_file()
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        saved = []
    merged = list(dict.fromkeys(DEFAULT_TOPICS + saved))
    return merged


def add_topic(name: str) -> bool:
    """Add a topic if not already present. Returns True if new."""
    topics = load_topics()
    clean = name.strip().title()
    if not clean or clean in topics:
        return False
    topics.append(clean)
    _ensure_file()
    _TOPICS_FILE.write_text(json.dumps(topics, indent=2), encoding="utf-8")
    return True


def extract_topic_from_filename(filename: str) -> str:
    """Intelligently extract a topic name from an uploaded filename.

    Examples:
        recursion_notes.pdf       → Recursion Notes
        Smart-Home-System.pdf     → Smart Home System
        binary_trees_advanced.md  → Binary Trees Advanced
    """
    stem = Path(filename).stem
    # Replace separators with spaces
    name = re.sub(r"[-_]+", " ", stem)
    # Remove noise words
    name = re.sub(r"\b(notes|summary|cheat\s*sheet|guide|draft|v\d+)\b", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip()
    return name.title() if name else stem.title()
