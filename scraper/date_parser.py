"""
scraper/date_parser.py
----------------------
Parse natural-language date strings into YYYY-MM-DD format.

Supports:
  - ISO format: "2025-08-15"
  - "today", "tomorrow"
  - "20 june", "20th june 2025", "june 20", "june 20th 2025"
  - DD/MM/YYYY, DD-MM-YYYY
"""

import re
from datetime import datetime, timedelta


# ─────────────────────────────────────────
# MONTH LOOKUP TABLE
# ─────────────────────────────────────────
MONTHS: dict[str, int] = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _resolve_year(year_str: str | None, month: int, day: int) -> int:
    """Pick the year that places this date in the future."""
    if year_str:
        yr = int(year_str)
        return yr + 2000 if yr < 100 else yr

    now = datetime.now()
    yr  = now.year
    try:
        if datetime(yr, month, day) < now:
            yr += 1
    except ValueError:
        pass
    return yr


def parse_date(raw: str) -> str:
    """
    Convert a raw date string to 'YYYY-MM-DD'.
    Raises ValueError when the string cannot be parsed.
    """
    raw = raw.strip().lower()

    # ── ISO format ────────────────────────────────────────────
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw

    # ── Relative ──────────────────────────────────────────────
    if raw == "today":
        return datetime.now().strftime("%Y-%m-%d")
    if raw == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # ── "20 june [2025]" or "20th june [2025]" ───────────────
    m = re.match(r"(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)(?:\s+(\d{2,4}))?", raw)
    if m:
        day, mon_str, yr_str = int(m.group(1)), m.group(2), m.group(3)
        mon = MONTHS.get(mon_str)
        if mon:
            yr = _resolve_year(yr_str, mon, day)
            try:
                return datetime(yr, mon, day).strftime("%Y-%m-%d")
            except ValueError:
                pass

    # ── "june 20 [2025]" or "june 20th [2025]" ───────────────
    m = re.match(r"([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+(\d{2,4}))?", raw)
    if m:
        mon_str, day, yr_str = m.group(1), int(m.group(2)), m.group(3)
        mon = MONTHS.get(mon_str)
        if mon:
            yr = _resolve_year(yr_str, mon, day)
            try:
                return datetime(yr, mon, day).strftime("%Y-%m-%d")
            except ValueError:
                pass

    # ── DD/MM/YYYY or DD-MM-YYYY ──────────────────────────────
    m = re.match(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", raw)
    if m:
        d, mo, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        yr = yr + 2000 if yr < 100 else yr
        try:
            return datetime(yr, mo, d).strftime("%Y-%m-%d")
        except ValueError:
            pass

    raise ValueError(f"Cannot parse date: '{raw}'")
