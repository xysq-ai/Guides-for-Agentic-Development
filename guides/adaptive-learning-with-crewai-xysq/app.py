"""Streamlit UI — Adaptive Learning Companion with Persistent Memory.

Run:  streamlit run app.py
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "1")
for _logger in ("litellm", "opentelemetry", "xysq", "httpx", "httpcore"):
    logging.getLogger(_logger).setLevel(logging.WARNING)

from xysq_crewai.crew import LearningCrew, AssessmentCrew
from xysq_crewai import memory_tools as mem
from xysq_crewai.topics import load_topics, add_topic, extract_topic_from_filename

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

MIME_MAP = {"pdf": "application/pdf", "txt": "text/plain", "md": "text/markdown"}
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
QUESTION_COUNTS = [3, 5, 10]

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Adaptive Learning Companion",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }

/* ── Header ── */
.app-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    padding: 2.5rem 3rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    color: white;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.app-header h1 { margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; }
.app-header p  { margin: 0.5rem 0 0; opacity: 0.85; font-size: 1rem; line-height: 1.5; font-weight: 400; }

/* ── Memory card (The core "Prior Learning Recalled" moment) ── */
.memory-card {
    background: #f0fdfa;
    border: 1px solid #99f6e4;
    border-left: 4px solid #0d9488;
    padding: 1.25rem 1.75rem;
    border-radius: 8px;
    color: #0f172a;
    margin-bottom: 2rem;
    font-size: 0.95rem;
    line-height: 1.6;
    box-shadow: 0 2px 4px rgba(13, 148, 136, 0.05);
}
.memory-card strong {
    display: block;
    font-size: 0.8rem;
    font-weight: 700;
    color: #0f766e;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Question card ── */
.question-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1.5rem 2rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
.question-num {
    font-size: 0.75rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
}
.question-text {
    font-size: 1.05rem;
    font-weight: 500;
    color: #0f172a;
    line-height: 1.6;
    margin: 0;
}

/* ── Review card ── */
.review-correct { border-left: 4px solid #10b981; }
.review-wrong   { border-left: 4px solid #ef4444; }

/* ── Score display ── */
.score-display {
    font-size: 4rem;
    font-weight: 700;
    color: #0f172a;
    text-align: center;
    line-height: 1;
    padding: 1rem 0 0.5rem;
    letter-spacing: -0.02em;
}
.score-label {
    text-align: center;
    font-size: 0.9rem;
    font-weight: 500;
    color: #64748b;
    margin-bottom: 1.5rem;
}

/* ── Memory update card ── */
.update-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1.5rem;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #334155;
}
.update-card strong { 
    display: block; 
    margin-bottom: 0.75rem; 
    font-weight: 600; 
    color: #0f172a;
}

/* ── Topic badge ── */
.topic-badge {
    display: inline-block;
    background: #f1f5f9;
    color: #475569;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    margin: 0.25rem;
    border: 1px solid #e2e8f0;
}

/* ── Sidebar tweaks ── */
section[data-testid="stSidebar"] .stRadio > div {
    gap: 6px;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.85rem;
}
section[data-testid="stSidebar"] .stFileUploader {
    margin-top: 0.25rem;
}
/* Fix duplicate / overlapping text on the file-uploader button.
   Hide ALL text inside the button, then overlay a single clean
   label via ::after so there's no ghost/duplicate text. */
div[data-testid="stFileUploader"] button,
section[data-testid="stSidebar"] .stFileUploader button {
    color: transparent !important;
    position: relative !important;
    overflow: hidden !important;
}
div[data-testid="stFileUploader"] button *,
section[data-testid="stSidebar"] .stFileUploader button * {
    color: transparent !important;
}
div[data-testid="stFileUploader"] button::after,
section[data-testid="stSidebar"] .stFileUploader button::after {
    content: "Upload" !important;
    color: inherit !important;
    color: rgba(255,255,255,0.9) !important;
    position: absolute !important;
    inset: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0.875rem !important;
    pointer-events: none !important;
}
.stFileUploader > label {
    margin-bottom: 10px;
}
section[data-testid="stSidebar"] .stMarkdown h5,
section[data-testid="stSidebar"] .stMarkdown strong {
    margin-bottom: 0;
    margin-top: 0.75rem;
    display: block;
}

/* ── Review answer indicator ── */
.ans-correct { color: #10b981; font-weight: 600; }
.ans-wrong   { color: #ef4444; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

_DEFAULTS: dict = dict(
    phase="select",
    topic="",
    difficulty="Intermediate",
    num_questions=5,
    memory_context="",
    lesson="",
    questions=[],   # list of dicts: question/options/correct_answer/explanation
    answers={},     # {question_index: chosen_option_str}
    score=0,
    total=0,
    evaluation="",
    report="",
    uploads=[],
)
for _k, _v in _DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


# ---------------------------------------------------------------------------
# Quiz parsing — robust JSON with text fallback
# ---------------------------------------------------------------------------

def _extract_json_array(text: str) -> str:
    """Pull the first [...] block out of a string that may have surrounding prose."""
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return ""


def _normalize_question(raw: dict) -> dict | None:
    """Validate and normalize a single question dict. Returns None if invalid."""
    q = raw.get("question", "").strip()
    opts = raw.get("options", [])
    ans = str(raw.get("correct_answer", raw.get("answer", ""))).strip().upper()
    expl = raw.get("explanation", "").strip()

    if not q or len(opts) != 4 or ans not in ("A", "B", "C", "D"):
        return None

    # Ensure options have "A) " prefix
    normalized_opts = []
    for i, opt in enumerate(opts):
        prefix = f"{chr(65 + i)}) "
        s = str(opt).strip()
        normalized_opts.append(s if s.startswith(prefix[0]) else prefix + s)

    return dict(question=q, options=normalized_opts, correct_answer=ans, explanation=expl)


def parse_quiz(raw_output: str) -> list[dict]:
    """Parse JSON quiz output from the LLM.

    Tries in order:
    1. Direct JSON parse of the full output.
    2. Extract the first [...] block and parse it.
    3. Returns empty list — caller shows a regenerate button.
    """
    if not raw_output or not raw_output.strip():
        return []

    candidates = [raw_output.strip(), _extract_json_array(raw_output)]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
            if isinstance(data, list):
                questions = [_normalize_question(q) for q in data if isinstance(q, dict)]
                valid = [q for q in questions if q is not None]
                if valid:
                    return valid
        except (json.JSONDecodeError, ValueError):
            continue

    return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def session_count() -> int:
    return len(list(REPORTS_DIR.glob("session_*.md")))


def save_report(topic: str, report_md: str) -> None:
    n = session_count() + 1
    path = REPORTS_DIR / f"session_{n}.md"
    header = f"# Session {n} — {topic}\n_{datetime.now():%Y-%m-%d %H:%M}_\n\n"
    path.write_text(header + report_md, encoding="utf-8")


def _score_answers(questions: list[dict], answers: dict) -> tuple[int, int]:
    correct = sum(
        1 for i, q in enumerate(questions)
        if answers.get(i, "").startswith(q["correct_answer"])
    )
    return correct, max(len(questions), 1)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🧠 Learning Companion")
    st.caption("Adaptive memory across sessions")

    st.divider()

    all_topics = load_topics()
    topic = st.selectbox("Choose a topic", all_topics)

    st.markdown("**Difficulty**")
    difficulty = st.radio(
        "Difficulty",
        options=DIFFICULTIES,
        index=1,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("**Questions**")
    num_questions = st.selectbox(
        "Number of questions",
        options=QUESTION_COUNTS,
        index=1,
        label_visibility="collapsed",
    )

    st.markdown("")
    if st.button("🚀 Start Session", use_container_width=True, type="primary"):
        st.session_state.update(_DEFAULTS)
        st.session_state.topic = topic
        st.session_state.difficulty = difficulty
        st.session_state.num_questions = num_questions
        st.session_state.phase = "learning"

    st.divider()
    st.markdown("##### 📄 Upload Material")

    uploaded = st.file_uploader(
        "PDF, TXT, or Markdown",
        type=["pdf", "txt", "md"],
    )
    if uploaded and uploaded.name not in st.session_state.uploads:
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        mime = MIME_MAP.get(ext, "application/octet-stream")
        with st.spinner(f"Uploading {uploaded.name}…"):
            status = mem.upload_document(uploaded.getvalue(), uploaded.name, mime)
        st.session_state.uploads.append(uploaded.name)

        extracted = extract_topic_from_filename(uploaded.name)
        is_new = add_topic(extracted)

        if status.startswith("✓"):
            st.success(status + (f"\n📌 **{extracted}** added to topics." if is_new else ""))
        else:
            st.warning(status)

        # Rerun so the selectbox re-renders with the newly added topic
        if is_new:
            st.rerun()

    if st.session_state.uploads:
        st.markdown("**Uploaded:**")
        for f in st.session_state.uploads:
            st.caption(f"📎 {f}")

    st.divider()
    st.caption(f"Sessions completed: **{session_count()}**")


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="app-header">'
    "<h1>🧠 Adaptive Learning System</h1>"
    "<p>Upload your knowledge · Learn interactively · Persist memory across sessions</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Phase: Select ──────────────────────────────────────────────────────────
if st.session_state.phase == "select":
    st.markdown("### Ready to learn.")
    st.caption("Select a topic from the sidebar, adjust your difficulty, and begin your session.")

    custom = [t for t in load_topics() if t not in [
        "Recursion", "Sorting Algorithms", "Binary Trees",
        "Graph Traversal", "Dynamic Programming",
    ]]
    if custom:
        st.markdown("<br>**Your uploaded knowledge:**", unsafe_allow_html=True)
        badges = " ".join(f'<span class="topic-badge">{t}</span>' for t in custom)
        st.markdown(badges, unsafe_allow_html=True)


# ── Phase: Learning ────────────────────────────────────────────────────────
elif st.session_state.phase == "learning":
    topic = st.session_state.topic
    difficulty = st.session_state.difficulty
    num_questions = st.session_state.num_questions

    with st.spinner("🧠 Recalling your learning history…"):
        context = mem.get_learning_context(topic)
        st.session_state.memory_context = context

    if "No prior" not in context:
        st.markdown(
            f'<div class="memory-card"><strong>🧠 Prior Learning Recalled</strong>{context}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="memory-card" style="border-left-color: #cbd5e1; background: #f8fafc; border-color: #e2e8f0;">'
            '<strong>🆕 First Session</strong>'
            'No prior learning history found for this topic. Let\'s establish a baseline.'
            '</div>',
            unsafe_allow_html=True,
        )

    with st.spinner(f"📚 Building {difficulty.lower()} lesson on **{topic}** ({num_questions} questions)…"):
        learning = LearningCrew()
        crew_instance = learning.crew()
        result = crew_instance.kickoff(inputs={
            "topic": topic,
            "memory_context": context,
            "difficulty": difficulty,
            "num_questions": str(num_questions),
        })

        # Lesson = first task output; quiz JSON = final crew output
        try:
            lesson = crew_instance.tasks[0].output.raw or ""
        except Exception:
            lesson = ""
        quiz_raw = result.raw or ""

    questions = parse_quiz(quiz_raw)

    st.session_state.lesson = lesson
    st.session_state.questions = questions
    st.session_state.answers = {}
    st.session_state.phase = "quiz" if questions else "quiz_failed"
    st.rerun()


# ── Phase: Quiz ────────────────────────────────────────────────────────────
elif st.session_state.phase == "quiz":
    topic = st.session_state.topic
    context = st.session_state.memory_context
    difficulty = st.session_state.difficulty
    questions = st.session_state.questions

    if "No prior" not in context:
        st.markdown(
            f'<div class="memory-card"><strong>🧠 Prior Learning Recalled</strong>{context}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="memory-card" style="border-left-color: #cbd5e1; background: #f8fafc; border-color: #e2e8f0;">'
            '<strong>🆕 First Session</strong>'
            'No prior learning history found for this topic. Let\'s establish a baseline.'
            '</div>',
            unsafe_allow_html=True,
        )

    with st.expander("📚 Review the Lesson", expanded=False):
        st.markdown(st.session_state.lesson or "_No lesson available._")

    st.markdown(f"### 🧪 Adaptive Quiz — {difficulty}")
    st.caption(f"{topic} · {len(questions)} questions")
    st.markdown("")

    for i, q in enumerate(questions):
        st.markdown(
            f'<div class="question-card">'
            f'<div class="question-num">Question {i + 1} of {len(questions)}</div>'
            f'<p class="question-text">{q["question"]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.radio(
            f"Answer for Q{i + 1}",
            q["options"],
            key=f"q_ans_{i}",
            label_visibility="collapsed",
        )
        st.markdown("")  # breathing room between questions

    if st.button("📝 Submit Answers", type="primary", use_container_width=True):
        answers = {i: st.session_state.get(f"q_ans_{i}", "") for i in range(len(questions))}
        st.session_state.answers = answers
        st.session_state.phase = "evaluating"
        st.rerun()


# ── Phase: Quiz Failed ──────────────────────────────────────────────────────
elif st.session_state.phase == "quiz_failed":
    st.warning(
        "⚠️ Quiz generation produced an unexpected format. "
        "Press **Regenerate** to try again."
    )
    if st.button("🔄 Regenerate Quiz", type="primary"):
        st.session_state.phase = "learning"
        st.rerun()


# ── Phase: Evaluating ──────────────────────────────────────────────────────
elif st.session_state.phase == "evaluating":
    topic = st.session_state.topic
    context = st.session_state.memory_context
    difficulty = st.session_state.difficulty
    num_questions = st.session_state.num_questions
    questions = st.session_state.questions
    answers = st.session_state.answers

    score, total = _score_answers(questions, answers)

    # Build readable answers text for the assessment crew
    lines = [
        f"Q{i + 1}: {q['question']}\n"
        f"Options: {', '.join(q['options'])}\n"
        f"Correct: {q['correct_answer']}\n"
        f"Learner chose: {answers.get(i, 'No answer')}"
        for i, q in enumerate(questions)
    ]
    answers_text = "\n\n".join(lines)

    with st.spinner("📊 Evaluating answers and generating progress report…"):
        assessment = AssessmentCrew()
        crew_instance = assessment.crew()
        report_result = crew_instance.kickoff(inputs={
            "topic": topic,
            "memory_context": context,
            "answers_text": answers_text,
            "evaluation": f"Score: {score}/{total}",
            "difficulty": difficulty,
            "num_questions": str(num_questions),
        })
        try:
            evaluation = crew_instance.tasks[0].output.raw or ""
        except Exception:
            evaluation = ""
        report_md = report_result.raw or ""

    st.session_state.evaluation = evaluation
    st.session_state.report = report_md
    st.session_state.score = score
    st.session_state.total = total

    # Persist session to xysq
    mem.store(
        f"Session on {topic} ({difficulty}, {total}q): scored {score}/{total}. {evaluation[:300]}",
        tags=[topic.lower().replace(" ", "-"), "session", difficulty.lower()],
        significance="high",
    )

    # Store understanding gaps separately for targeted future recall
    weak = [q["question"] for i, q in enumerate(questions)
            if not answers.get(i, "").startswith(q["correct_answer"])]
    if weak:
        mem.store(
            f"Understanding gaps in {topic} ({difficulty}): {'; '.join(weak)}",
            tags=[topic.lower().replace(" ", "-"), "gap"],
            significance="high",
        )

    save_report(topic, report_md)
    st.session_state.phase = "results"
    st.rerun()


# ── Phase: Results ─────────────────────────────────────────────────────────
elif st.session_state.phase == "results":
    topic = st.session_state.topic
    difficulty = st.session_state.difficulty
    questions = st.session_state.questions
    answers = st.session_state.answers
    score = st.session_state.score
    total = st.session_state.total
    pct = score / max(total, 1)

    # Score banner
    col_score, col_info = st.columns([1, 2])
    with col_score:
        st.markdown(f'<div class="score-display">{score}/{total}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-label">{difficulty} · {total} questions</div>', unsafe_allow_html=True)
        st.progress(pct)
    with col_info:
        st.markdown(f"### 📊 {topic}")
        if pct >= 0.8:
            st.success("🎉 Excellent — strong understanding demonstrated.")
        elif pct >= 0.5:
            st.warning("📈 Solid progress. A few areas need review.")
        else:
            st.error("💪 Keep going — focus on the gaps highlighted below.")
        st.caption(f"Session {session_count()} · {datetime.now():%B %d, %Y}")

    st.divider()

    # Question-by-question review
    st.markdown("### 📝 Review")
    for i, q in enumerate(questions):
        chosen = answers.get(i, "")
        is_correct = chosen.startswith(q["correct_answer"])
        status = "Correct" if is_correct else "Incorrect"
        label = f"Q{i + 1}  {status}  —  {q['question']}"
        with st.expander(label[:95] + ("..." if len(label) > 95 else ""), expanded=not is_correct):
            indicator_cls = "ans-correct" if is_correct else "ans-wrong"
            indicator_txt = "✓ Correct" if is_correct else "✗ Incorrect"
            st.markdown(
                f'<span class="{indicator_cls}">{indicator_txt}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**Your answer:** {chosen}")
            st.markdown(f"**Correct answer:** {q['correct_answer']}")
            if q.get("explanation"):
                st.info(q["explanation"])

    st.divider()

    # Report + memory update side by side
    col_rep, col_mem = st.columns([3, 2])
    with col_rep:
        st.markdown("### 📋 Progress Report")
        st.markdown(st.session_state.report or "_No report generated._")
    with col_mem:
        st.markdown("### 🧠 Memory Updated")
        st.markdown(
            '<div class="update-card">'
            "<strong>✓ Stored to persistent memory</strong>"
            f"<b>Topic:</b> {topic}<br>"
            f"<b>Difficulty:</b> {difficulty}<br>"
            f"<b>Score:</b> {score}/{total}<br><br>"
            "Your next session on this topic will adapt based on today's results."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")
    if st.button("🔄 Start New Session", type="primary", use_container_width=True):
        st.session_state.phase = "select"
        st.rerun()
