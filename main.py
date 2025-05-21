import os
import json
import asyncio
from dotenv import load_dotenv
from pathlib import Path
# Load environment variables from .env
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
import logging
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from handlers.currency import handle_currency
from handlers.unit import handle_unit
from handlers.start import start
from handlers.translate import get_handler as get_tl_handler
from handlers.translate_image import get_handler as get_tlpic_handler
from handlers.translate_audio import get_handler as get_tlvoice_handler
from handlers.remind import get_handlers as get_remind_handlers
from handlers.timezone import get_handler as get_timezone_handler

from scheduler import start_scheduler
from utils import parse_message, parse_unit_message, fetch_rates
from db.reminder_db import get_due_reminders, delete_reminder, get_recurring_reminders
from db.user_settings_db import get_user_timezone

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(Path(__file__).parent / "google_api.json")

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN missing in environment.")
        exit(1)

    fetch_rates()
    start_scheduler()

    app = Application.builder().token(TOKEN).build()

    async def smart_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if parse_message(text):
            await handle_currency(update, context)
        elif parse_unit_message(text):
            await handle_unit(update, context)

    async def reminder_scheduler(app):
        while True:
            reminders = get_due_reminders()
            for r in reminders:
                try:
                    await app.bot.send_message(chat_id=r['chat_id'], text=f"{r['remind_text']}")
                    delete_reminder(r['id'], r['chat_id'])
                except Exception as e:
                    print(f"Failed to send reminder {r['id']}: {e}")
            await asyncio.sleep(30)

    async def recurring_scheduler(app):
        while True:
            try:
                now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=pytz.UTC)
                recurring = get_recurring_reminders()
                for r in recurring:
                    tz_str = get_user_timezone(r['user_id']) or "Asia/Jakarta"
                    tz = pytz.timezone(tz_str)
                    local_now = now.astimezone(tz)
                    run_at = r['run_at'].astimezone(tz)

                    should_run = False
                    if r['recurrence'] == 'daily':
                        should_run = local_now.hour == 0 and local_now.minute == 0
                    elif r['recurrence'] == 'monthly':
                        should_run = (
                            local_now.day == run_at.day and
                            local_now.hour == 0 and local_now.minute == 0
                        )
                    elif r['recurrence'] == 'yearly':
                        should_run = (
                            local_now.month == run_at.month and
                            local_now.day == run_at.day and
                            local_now.hour == 0 and local_now.minute == 0
                        )

                    if should_run:
                        await app.bot.send_message(chat_id=r['chat_id'], text=f"🔁 Recurring Reminder:\n{r['remind_text']}")
            except Exception as e:
                print(f"[Recurring Scheduler Error] {e}")

            await asyncio.sleep(60)

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(get_tl_handler())
    app.add_handler(get_tlpic_handler())
    # app.add_handler(get_tlvoice_handler())
    for handler in get_remind_handlers():
        app.add_handler(handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_dispatcher))
    app.add_handler(get_timezone_handler())

    # Start schedulers
    asyncio.get_event_loop().create_task(reminder_scheduler(app))
    asyncio.get_event_loop().create_task(recurring_scheduler(app))

    app.run_polling()

if __name__ == "__main__":
    main()
