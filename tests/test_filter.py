"""
tests/test_filter.py
--------------------
Unit tests for the preference filter (no GPU, no network needed).
Run with: pytest tests/test_filter.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from agent.filter import apply_preference, build_flight_table


# ─── Sample data ──────────────────────────────────────────────
SAMPLE = [
    {
        "airline": "IndiGo", "price": 3200, "price_str": "Rs.3,200",
        "departure_str": "2025-08-15 06:10", "arrival_str": "2025-08-15 07:45",
        "duration": "1h 35m", "duration_min": 95,
        "stops": "Non-stop", "stops_raw": 0,
    },
    {
        "airline": "Air India", "price": 4800, "price_str": "Rs.4,800",
        "departure_str": "2025-08-15 14:00", "arrival_str": "2025-08-15 15:35",
        "duration": "1h 35m", "duration_min": 95,
        "stops": "Non-stop", "stops_raw": 0,
    },
    {
        "airline": "SpiceJet", "price": 2900, "price_str": "Rs.2,900",
        "departure_str": "2025-08-15 08:30", "arrival_str": "2025-08-15 11:00",
        "duration": "2h 30m", "duration_min": 150,
        "stops": "1 stop(s)", "stops_raw": 1,
    },
    {
        "airline": "Vistara", "price": 6500, "price_str": "Rs.6,500",
        "departure_str": "2025-08-15 19:00", "arrival_str": "2025-08-15 20:35",
        "duration": "1h 35m", "duration_min": 95,
        "stops": "Non-stop", "stops_raw": 0,
    },
]


def make_df():
    return pd.DataFrame(SAMPLE)


def test_cheapest_sort():
    df = make_df()
    filtered, label = apply_preference(df, "cheapest")
    assert filtered.iloc[0]["airline"] == "SpiceJet"   # 2900 is cheapest
    assert "price" in label


def test_non_stop_filter():
    df = make_df()
    filtered, label = apply_preference(df, "non-stop")
    assert all(filtered["stops_raw"] == 0)
    assert "non-stop" in label


def test_morning_filter():
    df = make_df()
    filtered, label = apply_preference(df, "morning flights")
    # Only 06:10 and 08:30 are before noon
    assert all(filtered["departure_str"].apply(lambda x: int(x[11:13])) < 12)


def test_evening_filter():
    df = make_df()
    filtered, label = apply_preference(df, "evening")
    # Only 19:00 is evening
    assert all(filtered["departure_str"].apply(lambda x: int(x[11:13])) >= 17)


def test_airline_filter():
    df = make_df()
    filtered, label = apply_preference(df, "indigo")
    assert all(filtered["airline"].str.lower().str.contains("indigo"))


def test_fastest_sort():
    df = make_df()
    filtered, label = apply_preference(df, "fastest")
    assert filtered.iloc[0]["duration_min"] == filtered["duration_min"].min()


def test_build_table_format():
    df = make_df()
    table = build_flight_table(df, "sorted by price", top_n=3)
    assert "1." in table
    assert "2." in table
    assert "3." in table
