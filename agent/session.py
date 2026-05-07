"""
agent/session.py
----------------
Conversation session state management.

A session is a plain dict so it serialises cleanly to/from Gradio gr.State.

Schema
------
{
    "stage":        str,   # collect | scraping | preference | pick | done
    "departure":    str | None,
    "destination":  str | None,
    "date":         str | None,   # YYYY-MM-DD
    "trip_type":    str,          # "one-way" | "round-trip"
    "date_adjusted": bool,
    "df":           list[dict] | None,   # raw scraper results
    "top5":         list[dict] | None,   # filtered top-5
    "chosen":       dict | None,
    "history":      list[dict],          # [{user, assistant}, ...]
}
"""

from __future__ import annotations

from config.settings import HISTORY_TURNS_SHOWN


# ─────────────────────────────────────────
# FACTORY
# ─────────────────────────────────────────
def new_session() -> dict:
    """Return a blank session ready for the 'collect' stage."""
    return {
        "stage":         "collect",
        "departure":     None,
        "destination":   None,
        "date":          None,
        "trip_type":     "one-way",
        "date_adjusted": False,
        "df":            None,
        "top5":          None,
        "chosen":        None,
        "history":       [],
    }


# ─────────────────────────────────────────
# HISTORY HELPERS
# ─────────────────────────────────────────
def append_history(session: dict, user: str, assistant: str) -> None:
    """Append a turn to session history in-place."""
    session.setdefault("history", [])
    session["history"].append({"user": user, "assistant": assistant})


def format_history(session: dict) -> str:
    """Return the last N turns as a readable string for the UI history box."""
    turns = session.get("history", [])[-HISTORY_TURNS_SHOWN:]
    return "\n".join(
        f"You: {t['user']}\nAgent: {t['assistant']}\n"
        for t in turns
    )


# ─────────────────────────────────────────
# MISSING FIELD HELPER
# ─────────────────────────────────────────
def missing_fields(session: dict) -> list[str]:
    """Return list of field names the agent still needs to collect."""
    needed = []
    if not session.get("departure"):   needed.append("departure city")
    if not session.get("destination"): needed.append("destination city")
    if not session.get("date"):        needed.append("travel date")
    return needed
