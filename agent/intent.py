"""
agent/intent.py
---------------
Extract departure city, destination city, date, and trip type
from a raw user utterance — WITHOUT calling the LLM.

Uses fast regex + optional airports.csv city matching as fallback.
The LLM is reserved for response generation (responder.py).
"""

from __future__ import annotations

import re
import pandas as pd
from datetime import datetime, timedelta

from config.settings import AIRPORTS_CSV


# ─────────────────────────────────────────
# LOAD CITY LIST FROM airports.csv
# ─────────────────────────────────────────
_known_cities: list[str] = []

if AIRPORTS_CSV.exists():
    try:
        _ap = pd.read_csv(AIRPORTS_CSV, on_bad_lines="skip", encoding="utf-8")
        if "city" in _ap.columns:
            _known_cities = _ap["city"].dropna().str.strip().unique().tolist()
    except Exception as exc:
        print(f"[intent] airports.csv load warning: {exc}")


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
_FILLER_RE = re.compile(
    r"\b(i want to|i want|book|flight ticket|ticket|please|can you|me|a)\b",
    re.I,
)
_FROM_RE   = re.compile(r"\bfrom\b", re.I)
_NOISE_RE  = re.compile(
    r"\b(today|tomorrow|one way|one-way|round trip|round-trip|flight|ticket)\b",
    re.I,
)

_TRIP_KEYWORDS: dict[str, str] = {
    "round trip":  "round-trip",
    "round-trip":  "round-trip",
    "return":      "round-trip",
    "one way":     "one-way",
    "one-way":     "one-way",
}


def _extract_route_regex(text: str) -> dict | None:
    """Fast regex: strip noise, find 'X to Y' pattern."""
    clean = _FILLER_RE.sub("", text)
    clean = _FROM_RE.sub("", clean)
    clean = _NOISE_RE.sub("", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    m = re.search(r"([a-zA-Z ]+?)\s+to\s+([a-zA-Z ]+)", clean, re.I)
    if not m:
        return None

    dep = m.group(1).strip().title()
    dst = m.group(2).strip().title()
    # trim trailing noise from destination
    dst = re.split(r"\b(flight|ticket)\b", dst, flags=re.I)[0].strip()

    if dep and dst:
        return {"departure": dep, "destination": dst}
    return None


def _extract_route_csv(text: str) -> dict | None:
    """Fallback: scan city list for two cities present in user text."""
    lower = text.lower()
    found = [c for c in _known_cities if c.lower() in lower]
    if len(found) >= 2:
        return {
            "departure":   found[0].title(),
            "destination": found[1].title(),
        }
    return None


def _extract_date(text: str) -> tuple[str | None, bool]:
    """
    Return (date_str, is_future_adjusted).
    date_str is YYYY-MM-DD or None.
    is_future_adjusted is True when the parsed date was in the past
    and we bumped it to +3 days from today.
    """
    lower = text.lower()
    today = datetime.now()

    if "tomorrow" in lower:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d"), False
    if "today" in lower:
        return today.strftime("%Y-%m-%d"), False

    # Look for explicit YYYY-MM-DD in the message
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if m:
        date_str = m.group(1)
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt < today + timedelta(days=1):
                return (today + timedelta(days=3)).strftime("%Y-%m-%d"), True
            return date_str, False
        except ValueError:
            pass

    return None, False


def _extract_trip_type(text: str) -> str:
    lower = text.lower()
    for phrase, trip in _TRIP_KEYWORDS.items():
        if phrase in lower:
            return trip
    return "one-way"


# ─────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────
def extract_intent(user_text: str) -> dict:
    """
    Parse a user utterance and return:

    {
        "departure":     str | None,
        "destination":   str | None,
        "date":          str | None,   # YYYY-MM-DD
        "trip_type":     str,          # "one-way" | "round-trip"
        "date_adjusted": bool,         # True if past date was bumped
    }
    """
    route = _extract_route_regex(user_text) or _extract_route_csv(user_text)
    date, date_adjusted = _extract_date(user_text)
    trip_type = _extract_trip_type(user_text)

    return {
        "departure":     route["departure"]   if route else None,
        "destination":   route["destination"] if route else None,
        "date":          date,
        "trip_type":     trip_type,
        "date_adjusted": date_adjusted,
    }
