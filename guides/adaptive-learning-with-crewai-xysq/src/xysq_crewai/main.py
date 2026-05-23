#!/usr/bin/env python
"""CLI entry point — run the adaptive learning crew from the terminal."""

import os
import sys
import warnings
import logging

from xysq_crewai.crew import LearningCrew, AssessmentCrew
from xysq_crewai.memory_tools import get_learning_context, store

# Suppress noisy framework output
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "1")


def run() -> None:
    """Run a single learning session from the command line."""
    topic = "Recursion"

    # Phase 1 — Recall
    print(f"\n🧠 Recalling learning history for '{topic}'...")
    context = get_learning_context(topic)
    if "No prior" in context:
        print("   First session — no prior history.\n")
    else:
        print("   ✓ Found prior learning context.\n")

    # Phase 2 — Learn + Quiz
    print(f"📚 Generating adaptive lesson + quiz for '{topic}'...")
    learning = LearningCrew()
    crew_instance = learning.crew()
    result = crew_instance.kickoff(
        inputs={"topic": topic, "memory_context": context, "difficulty": "Intermediate", "num_questions": "5"}
    )

    # Extract lesson from first task
    try:
        lesson = crew_instance.tasks[0].output.raw
    except Exception:
        lesson = ""
    quiz_raw = result.raw or ""

    print("\n--- Lesson ---")
    print(lesson[:500] if lesson else "(included in quiz output)")
    print("\n--- Quiz ---")
    print(quiz_raw[:800])

    # Phase 3 — Assessment
    answers_text = f"Quiz:\n{quiz_raw}\n\nLearner selected: A, B, C, A, D"
    print("\n📊 Evaluating answers...")

    assessment = AssessmentCrew()
    assessment_crew = assessment.crew()
    report = assessment_crew.kickoff(
        inputs={
            "topic": topic,
            "memory_context": context,
            "answers_text": answers_text,
            "evaluation": "Pending evaluation by agent",
            "difficulty": "Intermediate",
            "num_questions": "5",
        }
    )
    print("\n--- Progress Report ---")
    print(report.raw[:800] if report.raw else "(no report)")

    # Phase 4 — Store
    print("\n📝 Storing session to persistent memory...")
    status = store(
        f"Session completed for {topic}. {report.raw[:500]}",
        tags=[topic.lower().replace(" ", "-"), "session", "report"],
        significance="high",
    )
    print(f"   {status}")
    print("✓ Session complete.\n")


def train():
    """Train the crew for a given number of iterations."""
    inputs = {"topic": "Recursion", "memory_context": "No prior history.", "difficulty": "Intermediate", "num_questions": "5"}
    try:
        LearningCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"Training error: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        LearningCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"Replay error: {e}")


def test():
    """Test the crew execution."""
    inputs = {"topic": "Recursion", "memory_context": "No prior history.", "difficulty": "Intermediate", "num_questions": "5"}
    try:
        LearningCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"Test error: {e}")
