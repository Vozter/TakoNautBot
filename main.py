import os
from dotenv import load_dotenv
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from handlers.currency import handle_currency
from handlers.unit import handle_unit
from handlers.start import start
from scheduler import start_scheduler
from utils import parse_message, parse_unit_message, fetch_rates

# Load environment variables from .env
load_dotenv()

# Logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN missing in environment.")
    exit(1)

def main():
    fetch_rates()  # initial fetch on startup
    start_scheduler()

    app = Application.builder().token(TOKEN).build()

    async def smart_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if parse_message(text):
            await handle_currency(update, context)
        elif parse_unit_message(text):
            await handle_unit(update, context)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_dispatcher))

    app.run_polling()

if __name__ == "__main__":
    main()