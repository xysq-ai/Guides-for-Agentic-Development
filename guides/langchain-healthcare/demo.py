"""End-to-end simulated healthcare conversation across 3 LangChain agents.

Run each agent separately to see how memory persists across processes:

    python demo.py --intake     # patient describes symptoms; intake stores them
    python demo.py --doctor     # doctor recalls symptoms, diagnoses, prescribes
    python demo.py --pharm      # pharmacist recalls prescription, counsels

Patient turns are hardcoded so the run is deterministic — same output every time.
The whole point: same memory layer, three different processes, three different personas.
"""

import argparse
import asyncio
import os
import sys
import warnings

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, ToolMessage

import ui

load_dotenv()
warnings.filterwarnings("ignore")

if not os.getenv("XYSQ_API_KEY"):
    sys.exit("Missing XYSQ_API_KEY in .env — get one at https://app.xysq.ai/connect")
if not os.getenv("GOOGLE_API_KEY"):
    sys.exit("Missing GOOGLE_API_KEY in .env — get one at https://aistudio.google.com")

from agents import build_agent

PATIENT_TURNS = {
    "intake": [
        "Hi, I haven't been feeling great. I'm thirsty all the time and I'm "
        "going to the bathroom way more than usual, especially at night.",
        "It's been about two weeks. I've also lost maybe 12 pounds without trying, "
        "and I just feel exhausted by mid-afternoon.",
        "I'm 54. No real medical history, but my dad had diabetes.",
    ],
    "doctor": [
        "Hi Dr. Chen. The intake nurse said you'd review my case.",
        "What do you think is going on? Is there anything I should be doing now?",
    ],
    "pharm": [
        "Hi, I'm here to pick up my new prescription.",
        "Are there any side effects or things I should watch out for?",
    ],
}

SESSION_NUM = {"intake": 1, "doctor": 2, "pharm": 3}


def _final_text(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [c.get("text", "") for c in content if isinstance(c, dict)]
        return "\n".join(p for p in parts if p).strip()
    return str(content)


async def run_session(persona: str) -> None:
    ui.header(persona, SESSION_NUM[persona])
    agent = build_agent(persona)

    stored = 0
    recalled = 0
    history: list = []

    for patient_line in PATIENT_TURNS[persona]:
        ui.patient_turn(patient_line)
        history.append(("user", patient_line))

        result = await agent.ainvoke({"messages": history})
        new_messages = result["messages"][len(history):]

        for msg in new_messages:
            if isinstance(msg, ToolMessage):
                if msg.name == "store_memory":
                    stored += 1
                elif msg.name == "recall_memory":
                    recalled += 1
                ui.tool_result(str(msg.content))
            elif isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                for call in msg.tool_calls:
                    args_str = ", ".join(
                        f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}"
                        for k, v in call["args"].items()
                    )
                    ui.tool_call(call["name"], args_str)

        final = next(
            (m for m in reversed(result["messages"]) if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None)),
            None,
        )
        if final is not None:
            text = _final_text(final)
            if text:
                ui.agent_turn(persona, text)

        history = result["messages"]

    ui.session_summary(stored, recalled)


def main() -> None:
    parser = argparse.ArgumentParser(description="LangChain + xysq healthcare demo.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--intake", action="store_true", help="Run the intake agent.")
    group.add_argument("--doctor", action="store_true", help="Run the doctor agent.")
    group.add_argument("--pharm", action="store_true", help="Run the pharmacist agent.")
    args = parser.parse_args()

    persona = "intake" if args.intake else "doctor" if args.doctor else "pharm"
    asyncio.run(run_session(persona))


if __name__ == "__main__":
    main()
