"""xysq memory tools for LangChain agents.

Two @tool functions: recall_memory and store_memory.
Every agent in the demo gets exactly these two tools — that's the entire integration.
"""

import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from xysq import AsyncXysq

load_dotenv()
if not os.getenv("XYSQ_API_KEY"):
    raise RuntimeError("Missing XYSQ_API_KEY in .env")

client = AsyncXysq(api_key=os.environ["XYSQ_API_KEY"])


@tool
async def recall_memory(query: str) -> str:
    """Recall information from the patient's persistent memory.

    Use this whenever you need prior context: symptoms, diagnoses, prescriptions,
    or anything the patient has shared with another agent.
    """
    items = await client.memory.surface(query=query, budget="mid", domain="health")
    if not items:
        return "No relevant memory found."
    lines = [f"- {item.text}" for item in items[:5]]
    return "Recalled from memory:\n" + "\n".join(lines)


@tool
async def store_memory(content: str, tags: list[str] | None = None) -> str:
    """Store an important fact in the patient's persistent memory.

    Store one fact per call. Prefer specific facts ("polydipsia for 2 weeks")
    over summaries ("patient has symptoms").
    """
    result = await client.memory.capture(
        content=content,
        tags=tags or ["healthcare"],
        significance="high",
    )
    await client.memory.wait(result.memory_id, timeout=10, interval=0.5)
    return f"Stored: {content[:60]}{'...' if len(content) > 60 else ''}"
