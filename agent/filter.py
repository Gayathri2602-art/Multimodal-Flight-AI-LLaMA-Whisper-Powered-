"""
agent/filter.py
---------------
Parse user preference text and filter / sort a flight DataFrame.

Public API
----------
    apply_preference(df, user_text) -> (filtered_df, label_str)
"""

from __future__ import annotations

import pandas as pd


# ─────────────────────────────────────────
# KNOWN AIRLINE NAMES (lowercase)
# ─────────────────────────────────────────
_KNOWN_AIRLINES: list[str] = [
    "indigo", "air india", "spicejet", "vistara", "go first",
    "akasa", "emirates", "etihad", "qatar", "singapore airlines",
    "british airways", "lufthansa", "klm", "air france",
    "united", "delta", "american", "southwest",
]


def _dep_hour(row: pd.Series) -> int:
    """Extract hour from departure_str like '2025-05-10 06:45'. Default 12."""
    try:
        s = str(row["departure_str"])
        if len(s) >= 13:
            return int(s[11:13])
    except Exception:
        pass
    return 12


def _filter_time_of_day(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """
    period: 'morning' (< 12), 'afternoon' (12–17), 'evening' (>= 17)
    Returns filtered df, or original if filter yields nothing.
    """
    hours = df.apply(_dep_hour, axis=1)
    if period == "morning":
        mask = hours < 12
    elif period == "afternoon":
        mask = (hours >= 12) & (hours < 17)
    else:  # evening / night
        mask = hours >= 17

    filtered = df[mask]
    return filtered if not filtered.empty else df


# ─────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────
def apply_preference(df: pd.DataFrame, user_text: str) -> tuple[pd.DataFrame, str]:
    """
    Parse *user_text* for filter/sort preferences and apply them to *df*.

    Returns
    -------
    (result_df, label)
        result_df  — filtered and/or sorted DataFrame
        label      — human-readable summary of what was applied
    """
    u      = user_text.lower()
    result = df.copy()
    applied: list[str] = []

    # ── Non-stop filter ───────────────────────────────────────
    if any(w in u for w in ["non-stop", "nonstop", "non stop", "direct"]):
        ns = result[result["stops_raw"] == 0]
        if not ns.empty:
            result = ns
            applied.append("non-stop only")

    # ── Time-of-day filter ────────────────────────────────────
    if any(w in u for w in ["morning", "early"]):
        result = _filter_time_of_day(result, "morning")
        applied.append("morning departures (before 12 PM)")
    elif any(w in u for w in ["afternoon"]):
        result = _filter_time_of_day(result, "afternoon")
        applied.append("afternoon departures (12–5 PM)")
    elif any(w in u for w in ["evening", "night"]):
        result = _filter_time_of_day(result, "evening")
        applied.append("evening departures (after 5 PM)")

    # ── Airline filter ────────────────────────────────────────
    for airline in _KNOWN_AIRLINES:
        if airline in u:
            mask     = result["airline"].str.lower().str.contains(airline, regex=False)
            filtered = result[mask]
            if not filtered.empty:
                result = filtered
                applied.append(f"{airline.title()} flights")
            break   # only match one airline per turn

    # ── Sort ──────────────────────────────────────────────────
    if any(w in u for w in ["cheap", "cheapest", "lowest price", "price", "budget"]):
        result = result.sort_values("price")
        applied.append("sorted by price")
    elif any(w in u for w in ["fast", "fastest", "shortest", "quick", "duration"]):
        result = result.sort_values("duration_min")
        applied.append("sorted by duration")
    elif any(w in u for w in ["stop", "stops", "fewest stops"]):
        result = result.sort_values("stops_raw")
        applied.append("sorted by stops")
    else:
        result = result.sort_values("price")
        applied.append("sorted by price")

    label = ", ".join(applied) if applied else "sorted by price"
    return result, label


def build_flight_table(df: pd.DataFrame, label: str, top_n: int = 5) -> str:
    """
    Return a numbered plain-text table of the top *top_n* flights.

    Example output
    --------------
    Top 5 flights (non-stop only, sorted by price):

    1. IndiGo                       2025-05-10 06:10 -> 2025-05-10 07:45  1h 35m   Non-stop       Rs.3,200
    ...
    Reply with 1-5 to select, or ask for a different filter.
    """
    top = df.head(top_n)
    lines = [f"Top {len(top)} flights ({label}):\n"]

    for i, (_, r) in enumerate(top.iterrows(), 1):
        lines.append(
            f"{i}. {str(r['airline']):<30} "
            f"{r['departure_str']} -> {r['arrival_str']}  "
            f"{r['duration']:<8} {r['stops']:<14} "
            f"{r['price_str']}"
        )

    lines.append("\nReply with 1–5 to select, or ask for a different filter.")
    lines.append("(e.g. 'morning flights', 'IndiGo only', 'non-stop', 'cheapest')")
    return "\n".join(lines)
