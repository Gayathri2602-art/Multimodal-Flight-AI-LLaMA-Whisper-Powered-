"""
scraper/iata.py
---------------
City name  →  IATA airport code.

Priority order:
  1. Hard-coded overrides  (fastest, most reliable)
  2. airports.csv city column
  3. airports.csv name column
  4. Fuzzy substring match in airports.csv
  5. First-3-uppercase fallback with a warning
"""

import pandas as pd
from config.settings import AIRPORTS_CSV

# ─────────────────────────────────────────
# HARD-CODED OVERRIDES
# Common cities, aliases, and mis-spellings
# ─────────────────────────────────────────
IATA_OVERRIDES: dict[str, str] = {
    # India
    "mumbai": "BOM", "bombay": "BOM",
    "delhi": "DEL", "new delhi": "DEL",
    "bangalore": "BLR", "bengaluru": "BLR", "banglore": "BLR",
    "hyderabad": "HYD",
    "chennai": "MAA", "madras": "MAA",
    "kolkata": "CCU", "calcutta": "CCU",
    "goa": "GOI", "panaji": "GOI",
    "pune": "PNQ", "ahmedabad": "AMD",
    "jaipur": "JAI", "kochi": "COK", "cochin": "COK",
    "lucknow": "LKO", "nagpur": "NAG", "indore": "IDR",
    "bhubaneswar": "BBI",
    "vizag": "VTZ", "visakhapatnam": "VTZ",
    "surat": "STV", "amritsar": "ATQ", "varanasi": "VNS",
    "patna": "PAT", "ranchi": "IXR", "guwahati": "GAU",
    "coimbatore": "CJB",
    "thiruvananthapuram": "TRV", "trivandrum": "TRV",
    "mangalore": "IXE", "chandigarh": "IXC",
    # Middle East
    "dubai": "DXB", "abu dhabi": "AUH", "muscat": "MCT",
    "doha": "DOH", "riyadh": "RUH", "jeddah": "JED", "kuwait": "KWI",
    # Europe
    "london": "LHR", "paris": "CDG",
    "amsterdam": "AMS", "frankfurt": "FRA",
    "rome": "FCO", "madrid": "MAD", "barcelona": "BCN",
    "zurich": "ZRH", "vienna": "VIE", "brussels": "BRU",
    "copenhagen": "CPH", "stockholm": "ARN",
    "oslo": "OSL", "helsinki": "HEL", "athens": "ATH",
    "istanbul": "IST", "moscow": "SVO",
    # Asia-Pacific
    "singapore": "SIN", "bangkok": "BKK",
    "kuala lumpur": "KUL", "hong kong": "HKG",
    "tokyo": "NRT", "beijing": "PEK", "shanghai": "PVG",
    "seoul": "ICN", "taipei": "TPE",
    "manila": "MNL", "jakarta": "CGK",
    "sydney": "SYD", "melbourne": "MEL",
    # Americas
    "new york": "JFK", "nyc": "JFK",
    "los angeles": "LAX", "chicago": "ORD",
    "san francisco": "SFO", "miami": "MIA",
    "seattle": "SEA", "boston": "BOS",
    "washington": "IAD", "atlanta": "ATL",
    "denver": "DEN", "dallas": "DFW", "houston": "IAH",
    "phoenix": "PHX", "orlando": "MCO", "las vegas": "LAS",
    "new orleans": "MSY", "nashville": "BNA", "austin": "AUS",
    "toronto": "YYZ",
    "mexico city": "MEX", "sao paulo": "GRU",
    "buenos aires": "EZE", "lima": "LIM",
    "bogota": "BOG", "santiago": "SCL",
    # Africa / Others
    "cairo": "CAI", "nairobi": "NBO",
    "johannesburg": "JNB", "lagos": "LOS", "casablanca": "CMN",
    # South Asia
    "karachi": "KHI", "lahore": "LHE", "dhaka": "DAC",
    "colombo": "CMB", "kathmandu": "KTM",
    # Levant
    "tel aviv": "TLV", "amman": "AMM", "beirut": "BEY",
}

# ─────────────────────────────────────────
# CSV-backed lookup (loaded once at import)
# ─────────────────────────────────────────
_csv_city_to_iata: dict[str, str] = {}
_csv_name_to_iata: dict[str, str] = {}


def _load_airports_csv() -> None:
    """Populate the two CSV-backed dicts from airports.csv."""
    if not AIRPORTS_CSV.exists():
        return

    try:
        cols = [
            "code", "time_zone_id", "name", "city_code", "country_id",
            "location", "elevation", "url", "icao", "city", "county", "state",
        ]
        df = pd.read_csv(
            AIRPORTS_CSV, names=cols, header=0,
            on_bad_lines="skip", encoding="utf-8",
        )
        df = df.dropna(subset=["code"])
        df["code"] = df["code"].str.strip().str.upper()
        df["name"] = df["name"].fillna("").str.strip()
        df["city"] = df["city"].fillna("").str.strip()

        for _, row in df[df["name"].str.upper().str.contains("AIRPORT", na=False)].iterrows():
            k = row["city"].lower().strip()
            if k and k not in _csv_city_to_iata:
                _csv_city_to_iata[k] = row["code"]

        for _, row in df.iterrows():
            k = row["name"].lower().strip()
            if k:
                _csv_name_to_iata[k] = row["code"]

        print(f"[IATA] airports.csv loaded: {len(df)} airports")
    except Exception as exc:
        print(f"[IATA] Warning — airports.csv error: {exc}")


_load_airports_csv()


# ─────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────
def city_to_iata(city_name: str) -> str:
    """
    Convert a city name (or existing IATA code) to an IATA code.

    Raises ValueError if city_name is empty.
    Falls back to first-3-uppercase with a warning when no match is found.
    """
    if not city_name or not city_name.strip():
        raise ValueError("city_to_iata: city name must not be empty")

    raw   = city_name.strip()
    lower = raw.lower()

    # Already looks like an IATA code
    if len(raw) == 3 and raw.isalpha():
        return raw.upper()

    # 1. Hard-coded overrides
    if lower in IATA_OVERRIDES:
        return IATA_OVERRIDES[lower]

    # 2. CSV city column
    if lower in _csv_city_to_iata:
        return _csv_city_to_iata[lower]

    # 3. CSV name column
    if lower in _csv_name_to_iata:
        return _csv_name_to_iata[lower]

    # 4. Fuzzy substring match
    for city_key, code in _csv_city_to_iata.items():
        if lower in city_key or city_key in lower:
            return code

    # 5. Last-resort fallback
    code = raw.upper()[:3]
    print(f"[IATA] Warning: no match for '{city_name}', guessing '{code}'")
    return code


def iata_to_city(iata: str) -> str | None:
    """Reverse-lookup: IATA code → city name (best effort)."""
    iata = iata.strip().upper()
    for city, code in IATA_OVERRIDES.items():
        if code == iata:
            return city.title()
    return None
