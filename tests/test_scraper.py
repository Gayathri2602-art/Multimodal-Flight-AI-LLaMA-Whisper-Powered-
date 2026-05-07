"""
tests/test_scraper.py
---------------------
Unit tests for IATA lookup and date parser (no network needed).
Run with: pytest tests/test_scraper.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from scraper.iata import city_to_iata
from scraper.date_parser import parse_date
from datetime import datetime, timedelta


# ─── IATA lookup ──────────────────────────────────────────────

def test_iata_exact_code():
    assert city_to_iata("BOM") == "BOM"

def test_iata_mumbai():
    assert city_to_iata("Mumbai") == "BOM"

def test_iata_bombay_alias():
    assert city_to_iata("Bombay") == "BOM"

def test_iata_bangalore_variants():
    assert city_to_iata("Bangalore") == "BLR"
    assert city_to_iata("Bengaluru") == "BLR"
    assert city_to_iata("Banglore")  == "BLR"

def test_iata_goa():
    assert city_to_iata("Goa") == "GOI"

def test_iata_london():
    assert city_to_iata("London") == "LHR"

def test_iata_empty_raises():
    with pytest.raises(ValueError):
        city_to_iata("")


# ─── Date parser ──────────────────────────────────────────────

def test_date_iso():
    assert parse_date("2025-08-15") == "2025-08-15"

def test_date_tomorrow():
    expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert parse_date("tomorrow") == expected

def test_date_today():
    expected = datetime.now().strftime("%Y-%m-%d")
    assert parse_date("today") == expected

def test_date_natural_day_month():
    result = parse_date("20 june 2025")
    assert result == "2025-06-20"

def test_date_natural_month_day():
    result = parse_date("june 20 2025")
    assert result == "2025-06-20"

def test_date_ordinal():
    result = parse_date("15th august 2025")
    assert result == "2025-08-15"

def test_date_slash_format():
    result = parse_date("15/08/2025")
    assert result == "2025-08-15"

def test_date_invalid_raises():
    with pytest.raises(ValueError):
        parse_date("not a date at all")
