from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import pytz
from db.user_settings_db import set_user_timezone

async def timezone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /timezone <Timezone>\nExample: /timezone Asia/Tokyo")
        return

    tz_input = context.args[0].strip().title().replace('_', '/')
    if tz_input not in pytz.all_timezones:
        await update.message.reply_text("❌ Invalid timezone. Use values like Asia/Tokyo, Asia/Jakarta.\nSee: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")
        return

    set_user_timezone(update.effective_user.id, tz_input)
    await update.message.reply_text(f"✅ Timezone set to `{tz_input}`", parse_mode="Markdown")

def get_handler():
    return CommandHandler("timezone", timezone_command)
