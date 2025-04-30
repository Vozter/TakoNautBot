import re
import json
from datetime import datetime
import json
import logging
import requests
import os

logger = logging.getLogger(__name__)
OPEN_EXCHANGE_APP_ID = os.getenv("OPEN_EXCHANGE_APP_ID")
CACHE_FILE = "usd_rates.json"

def fetch_rates():
    from pathlib import Path
    if Path(CACHE_FILE).exists():
        try:
            with open(CACHE_FILE) as f:
                cache = json.load(f)
                last_time = datetime.fromisoformat(cache["timestamp"])
                now = datetime.utcnow()
                if last_time.year == now.year and last_time.month == now.month and last_time.day == now.day and last_time.hour == now.hour:
                    logger.info("Rates already fetched this hour. Skipping.")
                    return
        except Exception as e:
            logger.warning("Error reading cache. Proceeding to refetch.", exc_info=True)

    try:
        url = f"https://openexchangerates.org/api/latest.json?app_id={OPEN_EXCHANGE_APP_ID}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            with open(CACHE_FILE, "w") as f:
                json.dump({"timestamp": datetime.utcnow().isoformat(), "rates": data["rates"]}, f)
            logger.info("Exchange rates updated.")
        else:
            logger.error(f"Failed to fetch rates: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error("Network/API error while fetching rates:", exc_info=True)

def parse_message(text):
    match = re.match(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]{3})\s+to\s+([a-zA-Z]{3})", text.strip(), re.IGNORECASE)
    if match:
        amount = float(match.group(1))
        from_cur = match.group(2).upper()
        to_cur = match.group(3).upper()
        return amount, from_cur, to_cur
    return None


def convert_currency(amount, from_cur, to_cur):
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        rates = cache["rates"]
        from_rate = rates.get(from_cur)
        to_rate = rates.get(to_cur)
        if from_rate is None or to_rate is None:
            return None, None, None
        result = amount * (to_rate / from_rate)
        rate = to_rate / from_rate
        return result, rate, cache["timestamp"]
    except Exception:
        return None, None, None


def parse_unit_message(text):
    unit_keywords = {
        "kg": ["kg", "kilogram", "kilograms"],
        "lbs": ["lbs", "lb", "pound", "pounds"],
        "g": ["g", "gram", "grams"],
        "oz": ["oz", "ounce", "ounces"],
        "m": ["m", "meter", "meters"],
        "ft": ["ft", "foot", "feet"],
        "cm": ["cm", "centimeter", "centimeters"],
        "in": ["in", "inch", "inches"],
        "km": ["km", "kilometer", "kilometers"],
        "mi": ["mi", "mile", "miles"],
        "l": ["l", "liter", "liters"],
        "gal": ["gal", "gallon", "gallons"],
        "ml": ["ml", "milliliter", "milliliters"],
        "fl oz": ["fl oz", "fluid ounce", "fluid ounces"],
        "km/h": ["km/h", "kilometers per hour"],
        "mph": ["mph", "miles per hour"],
        "m/s": ["m/s", "meters per second"],
        "ft/s": ["ft/s", "feet per second"],
        "c": ["c", "celsius", "degree celsius"],
        "f": ["f", "fahrenheit", "degree fahrenheit"],
        "k": ["k", "kelvin"]
    }

    match = re.match(r"(\d+(?:\.\d+)?)\s*([a-zA-Z ]+)\s+to\s+([a-zA-Z ]+)", text.strip(), re.IGNORECASE)
    if match:
        amount = float(match.group(1))
        from_unit = match.group(2).strip().lower()
        to_unit = match.group(3).strip().lower()

        from_unit_key = next((key for key, aliases in unit_keywords.items() if from_unit in aliases), None)
        to_unit_key = next((key for key, aliases in unit_keywords.items() if to_unit in aliases), None)

        if from_unit_key and to_unit_key:
            return amount, from_unit_key, to_unit_key

    return None


def convert_unit(amount, from_unit, to_unit):
    conversions = {
        ("kg", "lbs"): 2.20462,
        ("lbs", "kg"): 0.453592,
        ("g", "oz"): 0.035274,
        ("oz", "g"): 28.3495,
        ("m", "ft"): 3.28084,
        ("ft", "m"): 0.3048,
        ("cm", "in"): 0.393701,
        ("in", "cm"): 2.54,
        ("km", "mi"): 0.621371,
        ("mi", "km"): 1.60934,
        ("l", "gal"): 0.264172,
        ("gal", "l"): 3.78541,
        ("ml", "fl oz"): 0.033814,
        ("fl oz", "ml"): 29.5735,
        ("km/h", "mph"): 0.621371,
        ("mph", "km/h"): 1.60934,
        ("m/s", "ft/s"): 3.28084,
        ("ft/s", "m/s"): 0.3048
    }

    if (from_unit, to_unit) in conversions:
        result = amount * conversions[(from_unit, to_unit)]
        return result, conversions[(from_unit, to_unit)]

    if from_unit == "c" and to_unit == "f":
        return (amount * 9/5) + 32, None
    elif from_unit == "f" and to_unit == "c":
        return (amount - 32) * 5/9, None
    elif from_unit == "c" and to_unit == "k":
        return amount + 273.15, None
    elif from_unit == "k" and to_unit == "c":
        return amount - 273.15, None
    elif from_unit == "f" and to_unit == "k":
        return (amount - 32) * 5/9 + 273.15, None
    elif from_unit == "k" and to_unit == "f":
        return (amount - 273.15) * 9/5 + 32, None

    return None, None


def format_rate(rate: float) -> str:
    if rate >= 1:
        return f"{rate:,.2f}"
    s = f"{rate:.10f}".rstrip("0")
    if "e" in s.lower():
        s = f"{rate:.15f}".rstrip("0")
    _, _, decimals = s.partition(".")
    leading_zeros = len(decimals) - len(decimals.lstrip("0"))
    precision = leading_zeros + 2
    return f"{rate:.{precision}f}".rstrip("0").rstrip(".")