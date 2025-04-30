import os
from dotenv import load_dotenv
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import re
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# === CONFIG ===
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Load from environment variable
OPEN_EXCHANGE_APP_ID = os.getenv("OPEN_EXCHANGE_APP_ID")  # Load from environment variable
CACHE_FILE = "usd_rates.json"

# === Environment Variable Validation ===
if not TOKEN or not OPEN_EXCHANGE_APP_ID:
    logger.error("Environment variables TELEGRAM_BOT_TOKEN or OPEN_EXCHANGE_APP_ID are missing.")
    exit(1)

# === Currency Rate Fetcher ===
def fetch_rates():
    from pathlib import Path

    # Check if cache exists
    if Path(CACHE_FILE).exists():
        try:
            with open(CACHE_FILE) as f:
                cache = json.load(f)
                last_time = datetime.fromisoformat(cache["timestamp"])
                now = datetime.utcnow()

                # If same year, month, day, and hour — skip update
                if (
                    last_time.year == now.year and
                    last_time.month == now.month and
                    last_time.day == now.day and
                    last_time.hour == now.hour
                ):
                    logger.info(f"[{datetime.now()}] Rates already fetched this hour. Skipping.")
                    return
        except json.JSONDecodeError:
            logger.warning("Cache file is corrupted. Refetching rates.")
        except Exception as e:
            logger.error("Unexpected error reading cache file:", exc_info=True)

    # Fetch from API
    try:
        url = f"https://openexchangerates.org/api/latest.json?app_id={OPEN_EXCHANGE_APP_ID}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            with open(CACHE_FILE, "w") as f:
                json.dump({
                    "timestamp": datetime.utcnow().isoformat(),
                    "rates": data["rates"]
                }, f)
            logger.info(f"[{datetime.now()}] Exchange rates updated.")
        else:
            logger.error(f"Failed to fetch rates: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logger.error("Network error while fetching rates:", exc_info=True)
    except Exception as e:
        logger.error("Unexpected error during fetch:", exc_info=True)

# === Conversion Handler ===
def parse_message(text):
    match = re.match(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]{3})\s+to\s+([a-zA-Z]{3})", text.strip(), re.IGNORECASE)
    if match:
        amount = float(match.group(1))
        from_cur = match.group(2).upper()
        to_cur = match.group(3).upper()
        return amount, from_cur, to_cur
    return None

# === Enhanced Logging in convert_currency ===
def convert_currency(amount, from_cur, to_cur):
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        rates = cache["rates"]
        from_rate = rates.get(from_cur)
        to_rate = rates.get(to_cur)
        if from_rate is None or to_rate is None:
            logger.warning(f"Currency code not found: {from_cur} or {to_cur}")
            return None, None, None
        result = amount * (to_rate / from_rate)
        rate = to_rate / from_rate
        logger.info(f"Converted {amount} {from_cur} to {result} {to_cur} at rate {rate}")
        return result, rate, cache["timestamp"]
    except FileNotFoundError:
        logger.error("Cache file not found. Please fetch rates first.")
        return None, None, None
    except json.JSONDecodeError:
        logger.error("Cache file is corrupted. Please refetch rates.")
        return None, None, None
    except Exception as e:
        logger.error("Unexpected error during conversion:", exc_info=True)
        return None, None, None

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parsed = parse_message(update.message.text)
    if not parsed:
        return

    amount, from_cur, to_cur = parsed
    result, rate, timestamp = convert_currency(amount, from_cur, to_cur)

    if result is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Conversion failed. Check currency codes or try again later.",
            message_thread_id=update.message.message_thread_id,
            reply_to_message_id=update.message.message_id
        )
        return

    time_str = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"*{format_rate(amount)} {from_cur}* = *{format_rate(result)} {to_cur}*\n"
        f"`1 {from_cur} = {format_rate(rate)} {to_cur}`\n"
        f"_(Rates last updated: {time_str})_"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        parse_mode="Markdown",
        message_thread_id=update.message.message_thread_id,
        reply_to_message_id=update.message.message_id
    )

def format_rate(rate: float) -> str:
    if rate >= 1:
        return f"{rate:,.2f}"

    # Convert to string with high precision, remove trailing zeros
    s = f"{rate:.10f}".rstrip("0")
    _, _, decimals = s.partition(".")

    # Count leading zeros after the decimal
    leading_zeros = 0
    for c in decimals:
        if c == "0":
            leading_zeros += 1
        else:
            break

    # Total precision = leading zeros + 2 more
    precision = leading_zeros + 2
    formatted = f"{rate:.{precision}f}".rstrip("0").rstrip(".")

    return formatted  # keep dot as decimal

# === Unit Conversion Handler ===
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

        # Normalize units
        from_unit_key = next((key for key, aliases in unit_keywords.items() if from_unit in aliases), None)
        to_unit_key = next((key for key, aliases in unit_keywords.items() if to_unit in aliases), None)

        if from_unit_key and to_unit_key:
            return amount, from_unit_key, to_unit_key

    return None

def convert_unit(amount, from_unit, to_unit):
    unit_conversions = {
        # Weight and Mass
        ("kg", "lbs"): 2.20462,
        ("lbs", "kg"): 0.453592,
        ("g", "oz"): 0.035274,
        ("oz", "g"): 28.3495,

        # Length and Distance
        ("m", "ft"): 3.28084,
        ("ft", "m"): 0.3048,
        ("cm", "in"): 0.393701,
        ("in", "cm"): 2.54,
        ("km", "mi"): 0.621371,
        ("mi", "km"): 1.60934,

        # Volume
        ("l", "gal"): 0.264172,
        ("gal", "l"): 3.78541,
        ("ml", "fl oz"): 0.033814,
        ("fl oz", "ml"): 29.5735,

        # Speed
        ("km/h", "mph"): 0.621371,
        ("mph", "km/h"): 1.60934,
        ("m/s", "ft/s"): 3.28084,
        ("ft/s", "m/s"): 0.3048,

        # Temperature (special handling required)
    }

    if (from_unit, to_unit) in unit_conversions:
        conversion_rate = unit_conversions[(from_unit, to_unit)]
        result = amount * conversion_rate
        return result, conversion_rate

    # Handle temperature conversions
    if from_unit == "c" and to_unit == "f":
        result = (amount * 9/5) + 32
        return result, None
    elif from_unit == "f" and to_unit == "c":
        result = (amount - 32) * 5/9
        return result, None
    elif from_unit == "c" and to_unit == "k":
        result = amount + 273.15
        return result, None
    elif from_unit == "k" and to_unit == "c":
        result = amount - 273.15
        return result, None
    elif from_unit == "f" and to_unit == "k":
        result = (amount - 32) * 5/9 + 273.15
        return result, None
    elif from_unit == "k" and to_unit == "f":
        result = (amount - 273.15) * 9/5 + 32
        return result, None

    return None, None

async def convert_units(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parsed = parse_unit_message(update.message.text)
    if not parsed:
        return

    amount, from_unit, to_unit = parsed
    result, conversion_rate = convert_unit(amount, from_unit, to_unit)

    if result is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Conversion failed. Check unit codes or try again later.",
            message_thread_id=update.message.message_thread_id,
            reply_to_message_id=update.message.message_id
        )
        return

    if from_unit in ["c", "f", "k"] or to_unit in ["c", "f", "k"]:
        msg = (
            f"*{format_rate(amount)}° {from_unit.upper()}* = *{format_rate(result)}° {to_unit.upper()}*"
        )
    else:
        msg = (
            f"*{format_rate(amount)} {from_unit}* = *{format_rate(result)} {to_unit}*\n"
            f"`1 {from_unit} = {format_rate(conversion_rate)} {to_unit}`"
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        parse_mode="Markdown",
        message_thread_id=update.message.message_thread_id,
        reply_to_message_id=update.message.message_id
    )

# === Scheduler Setup ===
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_rates, CronTrigger(minute=1))  # Runs every hour at hh:01
    scheduler.start()
    logger.info("Scheduler started.")

# === Main Bot ===
def main():
    fetch_rates()  # Initial fetch
    start_scheduler()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Regex(r"\d+\s*[a-zA-Z]{3}\s+to\s+[a-zA-Z]{3}"), convert))
    app.add_handler(MessageHandler(filters.Regex(r"\d+\s*[a-zA-Z]+\s+to\s+[a-zA-Z]+"), convert_units))
    app.run_polling()

if __name__ == "__main__":
    main()
