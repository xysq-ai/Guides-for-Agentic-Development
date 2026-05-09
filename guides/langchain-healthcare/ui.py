"""Pretty terminal UI helpers (rich-based)."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

PERSONA_STYLE = {
    "intake": ("Intake Assistant", "cyan"),
    "doctor": ("Dr. Chen", "green"),
    "pharm": ("Pharmacist", "magenta"),
}


def header(persona: str, session_num: int) -> None:
    label, color = PERSONA_STYLE[persona]
    console.print()
    console.rule(f"[bold {color}]Session {session_num} — {label}[/]", style=color)
    console.print()


def patient_turn(text: str) -> None:
    console.print(
        Panel(
            Text(text, style="white"),
            title="[bold yellow]Patient[/]",
            border_style="yellow",
            padding=(0, 1),
        )
    )


def agent_turn(persona: str, text: str) -> None:
    label, color = PERSONA_STYLE[persona]
    console.print(
        Panel(
            Text(text, style="white"),
            title=f"[bold {color}]{label}[/]",
            border_style=color,
            padding=(0, 1),
        )
    )


def tool_call(name: str, payload: str) -> None:
    truncated = payload if len(payload) <= 100 else payload[:97] + "..."
    console.print(f"  [dim]↳ tool: {name}({truncated})[/]")


def tool_result(text: str) -> None:
    truncated = text if len(text) <= 200 else text[:197] + "..."
    console.print(f"  [dim]  → {truncated}[/]")
    console.print()


def session_summary(stored: int, recalled: int) -> None:
    console.print()
    console.rule("[dim]session complete[/]", style="dim")
    console.print(
        f"  [dim]{stored} memories stored · {recalled} memories recalled[/]"
    )
    console.print()
