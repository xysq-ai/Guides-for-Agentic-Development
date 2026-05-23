"""xysq persistent memory layer for adaptive learning.

Thin wrapper around the xysq SDK — every function returns plain strings
or lists so the rest of the app never touches raw SDK objects.

Design:
  • surface() for all recall — fast, reliable, no heavy reflection
  • synthesize() only for post-session summaries — used sparingly
  • All errors resolve to calm fallback messages, never raw tracebacks
"""

from __future__ import annotations

import logging
from functools import lru_cache

from dotenv import load_dotenv
from xysq import Xysq

load_dotenv()

# Suppress noisy SDK / HTTP logs from surfacing in Streamlit
logging.getLogger("xysq").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _client() -> Xysq:
    return Xysq()


# ---------------------------------------------------------------------------
# Core memory operations
# ---------------------------------------------------------------------------

def store(
    content: str,
    *,
    tags: list[str] | None = None,
    significance: str = "normal",
) -> str:
    """Capture a learning memory permanently."""
    try:
        _client().memory.capture(
            content=content,
            tags=tags or [],
            significance=significance,
            scope="permanent",
        )
        return "✓ Memory stored"
    except Exception:
        return "⚠ Memory temporarily unavailable — continuing without storing."


# Keywords that indicate a memory is study/learning-related
_STUDY_SIGNALS = (
    "session", "score", "quiz", "gap", "learn", "study",
    "topic", "question", "understanding", "lesson",
    "assessment", "progress", "difficulty", "beginner",
    "intermediate", "advanced", "correct", "incorrect",
    "uploaded", "material", "document",
)


def _is_study_related(text: str) -> bool:
    """Quick heuristic: does this memory look like it came from a study session?"""
    lower = text.lower()
    return any(kw in lower for kw in _STUDY_SIGNALS)


def recall(query: str, *, budget: str = "low") -> list[str]:
    """Surface relevant *learning* memories only. Filters out non-study chat."""
    try:
        memories = _client().memory.surface(
            query,
            budget=budget,
            intent="learning",       # tell xysq we want educational content
            domain="education",      # scope to the education domain
        )
        # Post-filter: drop anything that slipped through and isn't study-related
        return [m.text for m in memories if _is_study_related(m.text)]
    except Exception:
        return []


def synthesize(query: str) -> str:
    """Ask a natural-language question answered from memory.

    Use sparingly — only for progress summaries, not for startup recall.
    """
    try:
        result = _client().memory.synthesize(query, budget="low")
        return result.answer or ""
    except Exception:
        return ""


def get_learning_context(topic: str) -> str:
    """Build learning context for *topic* using surface() only.

    No synthesize() call here — avoids the heavy /reflect endpoint
    that causes timeouts on startup.

    The query is tightly scoped to study-session language so xysq
    prioritises learning memories over casual chat.
    """
    # Very specific query — anchored to study-session vocabulary
    memories = recall(
        f"{topic} study session quiz score learning progress understanding gaps results"
    )

    if not memories:
        return "No prior learning history found."

    return "Prior learning history:\n" + "\n".join(f"• {m}" for m in memories[:5])


# ---------------------------------------------------------------------------
# Document uploads (xysq Organise)
# ---------------------------------------------------------------------------

_folder_id: str | None = None


def _ensure_folder() -> str:
    """Get or create the learning-materials folder (cached after first call)."""
    global _folder_id
    if _folder_id is not None:
        return _folder_id

    client = _client()
    try:
        folder = client.organise.create_folder("learning-materials")
        _folder_id = folder.id
    except Exception:
        for f in client.organise.list_folders():
            if getattr(f, "name", None) in ("learning-materials", "student-materials"):
                _folder_id = f.id
                break
    if _folder_id is None:
        raise RuntimeError("Could not create or find learning-materials folder")
    return _folder_id


def upload_document(content: bytes, filename: str, mime_type: str) -> str:
    """Upload a document to xysq Organise and wait for extraction."""
    try:
        client = _client()
        folder_id = _ensure_folder()

        file = client.organise.upload_file(
            content=content,
            filename=filename,
            mime_type=mime_type,
            folder_id=folder_id,
        )
        status = client.organise.wait_for_file(file.asset_id, timeout=60.0)

        if status.extraction_status == "ready":
            return f"✓ {filename} added to persistent learning memory"
        return f"⚠ {filename} uploaded (extraction: {status.extraction_status})"
    except Exception:
        return f"⚠ Upload for {filename} temporarily unavailable."
