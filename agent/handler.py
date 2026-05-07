"""
agent/handler.py
----------------
Orchestrates the multi-turn conversation using a finite state machine.

Stages
------
  collect    → gather departure, destination, date from user
  scraping   → call scraper, cache result, show summary
  preference → user states a filter (cheapest / morning / IndiGo …)
  pick       → user picks 1-5 from the table
  done       → booking confirmed

Public API
----------
    handle_turn(user_text, session, llm_model, tokenizer) -> (response_str, session)
"""

from __future__ import annotations

import re
import pandas as pd
from datetime import datetime

from agent.intent import extract_intent
from agent.filter import apply_preference, build_flight_table
from agent.session import new_session, missing_fields
from agent.responder import describe_flights, confirm_booking
from scraper.flights import scrape


# ─────────────────────────────────────────
# RESET KEYWORDS
# ─────────────────────────────────────────
_RESET_WORDS = {"reset", "restart", "new search", "start over", "new flight"}

_WORD_TO_NUM = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
}


# ─────────────────────────────────────────
# MAIN HANDLER
# ─────────────────────────────────────────
def handle_turn(
    user_text:  str,
    session:    dict,
    llm_model=None,
    tokenizer=None,
) -> tuple[str, dict]:
    """
    Process one user turn and return (agent_response, updated_session).

    llm_model / tokenizer are only needed in the 'pick' stage (confirmation).
    They can be None when running tests for earlier stages.
    """
    u = user_text.lower().strip()

    # ── Reset ─────────────────────────────────────────────────
    if any(w in u for w in _RESET_WORDS):
        session.update(new_session())
        return "Starting fresh! Tell me where and when you want to fly.", session

    # ══════════════════════════════════════════════════════════
    # STAGE: collect
    # ══════════════════════════════════════════════════════════
    if session["stage"] == "collect":
        intent = extract_intent(user_text)
        print(f"[handler] Intent: {intent}")

        if intent.get("departure"):     session["departure"]     = intent["departure"]
        if intent.get("destination"):   session["destination"]   = intent["destination"]
        if intent.get("date"):          session["date"]          = intent["date"]
        if intent.get("trip_type"):     session["trip_type"]     = intent["trip_type"]
        if intent.get("date_adjusted"): session["date_adjusted"] = intent["date_adjusted"]

        missing = missing_fields(session)
        if missing:
            return f"Got it! Could you also tell me your {', '.join(missing)}?", session

        # All info collected → proceed to scrape
        session["stage"] = "scraping"
        return handle_turn("__scrape__", session, llm_model, tokenizer)

    # ══════════════════════════════════════════════════════════
    # STAGE: scraping
    # ══════════════════════════════════════════════════════════
    if session["stage"] == "scraping":
        dep  = session["departure"]
        dst  = session["destination"]
        date = session["date"]
        trip = session["trip_type"]

        try:
            rows = scrape(dep, dst, date, trip=trip)
        except Exception as exc:
            session.update(new_session())
            return (
                f"Could not fetch flights from {dep} to {dst} on {date}. "
                f"Error: {str(exc)[:120]}. Please try again.",
                session,
            )

        if not rows:
            session.update(new_session())
            return (
                f"Sorry, no flights found from {dep} to {dst} on {date}. "
                "Try a different date or route.",
                session,
            )

        df = pd.DataFrame(rows)
        session["df"]    = df.to_dict(orient="records")  # store as list for gr.State
        session["stage"] = "preference"

        pretty_date = datetime.strptime(date, "%Y-%m-%d").strftime("%b %d")

        note = ""
        if session.get("date_adjusted"):
            note = (
                f"Note: I adjusted the date to {pretty_date} for better availability.\n\n"
            )

        return note + describe_flights(df, dep, dst, pretty_date), session

    # ══════════════════════════════════════════════════════════
    # STAGE: preference
    # ══════════════════════════════════════════════════════════
    if session["stage"] == "preference":
        df       = pd.DataFrame(session["df"])
        filtered, label = apply_preference(df, user_text)

        if filtered.empty:
            return (
                "No flights match that filter. "
                "Try: cheapest / morning / evening / non-stop / airline name.",
                session,
            )

        session["top5"]  = filtered.head(5).to_dict(orient="records")
        session["stage"] = "pick"
        return build_flight_table(filtered, label), session

    # ══════════════════════════════════════════════════════════
    # STAGE: pick
    # ══════════════════════════════════════════════════════════
    if session["stage"] == "pick":
        # Normalise word-numbers
        for word, num in _WORD_TO_NUM.items():
            u = u.replace(word, num)

        nums = re.findall(r"\b([1-5])\b", u)
        if nums:
            idx    = int(nums[0]) - 1
            chosen = session["top5"][idx]
            session["chosen"] = chosen
            session["stage"]  = "done"

            if llm_model and tokenizer:
                reply = confirm_booking(chosen, llm_model, tokenizer)
            else:
                # Fallback if no model loaded (tests / CLI)
                reply = (
                    f"Great! Your {chosen['airline']} flight at {chosen['price_str']} "
                    "is confirmed. Our agent will contact you for payment. Safe travels! ✈️"
                )
            return reply, session

        # No number found → re-apply as a preference filter
        session["stage"] = "preference"
        return handle_turn(user_text, session, llm_model, tokenizer)

    # ══════════════════════════════════════════════════════════
    # STAGE: done
    # ══════════════════════════════════════════════════════════
    if session["stage"] == "done":
        return (
            "Your booking is confirmed! Our agent will contact you for payment. "
            'Type "reset" to search for another flight.',
            session,
        )

    return 'Something went wrong. Type "reset" to start over.', session
