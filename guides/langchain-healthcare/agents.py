"""Agent factory — every agent is the same code with a different prompt.

The point of this file: building a memory-backed LangChain agent is one function.
Swap the prompt, you swap the persona. The memory layer doesn't change.
"""

import os
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from memory_tools import recall_memory, store_memory

MODEL = "gemini-2.5-flash"
PROMPTS_DIR = Path(__file__).parent / "prompts"


def build_agent(persona: str):
    """Build a LangChain agent for a given persona (intake, doctor, pharm)."""
    prompt_path = PROMPTS_DIR / f"{persona}.txt"
    system_prompt = prompt_path.read_text()

    llm = ChatGoogleGenerativeAI(
        model=MODEL,
        temperature=0.2,
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )
    return create_react_agent(
        model=llm,
        tools=[recall_memory, store_memory],
        state_modifier=system_prompt,
    )
