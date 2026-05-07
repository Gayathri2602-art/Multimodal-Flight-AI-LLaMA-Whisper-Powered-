"""
tests/test_intent.py
--------------------
Unit tests for the intent extractor (no GPU needed).
Run with: pytest tests/test_intent.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.intent import extract_intent


def test_basic_route():
    result = extract_intent("Goa to Bangalore tomorrow")
    assert result["departure"]   == "Goa"
    assert result["destination"] == "Bangalore"
    assert result["date"] is not None


def test_round_trip():
    result = extract_intent("Mumbai to Delhi round trip")
    assert result["trip_type"] == "round-trip"


def test_one_way():
    result = extract_intent("Chennai to Hyderabad one way")
    assert result["trip_type"] == "one-way"


def test_with_filler_words():
    result = extract_intent("I want to book a flight from Pune to Kochi")
    assert result["departure"]   == "Pune"
    assert result["destination"] == "Kochi"


def test_today():
    result = extract_intent("Delhi to Mumbai today")
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    assert result["date"] == today


def test_tomorrow():
    result = extract_intent("Kolkata to Bangalore tomorrow")
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert result["date"] == tomorrow


def test_missing_destination():
    result = extract_intent("fly from Mumbai")
    # Should have departure but no destination
    assert result["destination"] is None


def test_missing_all():
    result = extract_intent("hello there")
    assert result["departure"]   is None
    assert result["destination"] is None
