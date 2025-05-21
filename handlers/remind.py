from telegram import Update, ChatMember, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from db.reminder_db import add_reminder, get_reminders_by_chat, delete_reminder_by_id
from db.user_settings_db import get_user_timezone
import pytz
from datetime import datetime, timedelta
import re
import math
from telegram.helpers import escape_markdown

GLOBAL_ADMINS = [541766689]

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2,
    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
}

def parse_flexible_time(text: str, now: datetime, force_timezone: str = None) -> datetime | None:
    try:
        text = text.strip().lower()
        text = text.replace("minutes", "m").replace("minute", "m").replace("mins", "m").replace("min", "m")
        text = text.replace("hours", "h").replace("hour", "h").replace("hrs", "h").replace("hr", "h")
        text = text.replace("days", "d").replace("day", "d")
        normalized = re.sub(r'\s+', '', text)

        tz = pytz.timezone(force_timezone) if force_timezone else now.tzinfo or pytz.timezone("Asia/Jakarta")

        if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", text):
            return tz.localize(datetime.strptime(text, "%Y-%m-%d %H:%M"))

        abs_match = re.fullmatch(r"(\d{1,2})\s+([a-z]+)(?:\s+(\d{4}))?", text)
        if abs_match:
            day = int(abs_match.group(1))
            month_str = abs_match.group(2).title()
            year = int(abs_match.group(3)) if abs_match.group(3) else now.year
            try:
                month = datetime.strptime(month_str[:3], "%b").month
            except ValueError:
                month = datetime.strptime(month_str, "%B").month
            return tz.localize(datetime(year, month, day, 0, 0))

        delta = timedelta()
        for match in re.finditer(r"(\d+)([dhm])", normalized):
            val, unit = int(match.group(1)), match.group(2)
            if unit == "d": delta += timedelta(days=val)
            elif unit == "h": delta += timedelta(hours=val)
            elif unit == "m": delta += timedelta(minutes=val)

        return now + delta if delta > timedelta(0) else None
    except:
        return None

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id

    if user_id in GLOBAL_ADMINS:
        return True

    if update.effective_chat.type == "private":
        return True

    member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    return member.status in ["creator", "administrator"]

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command in groups.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage:\n/remind 10m message\n/remind daily msg\n/remind monthly 11 msg\n/remind yearly 12 October msg\n/remind weekly Monday msg")
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    recurrence = "once"
    gmt7 = pytz.timezone("Asia/Jakarta")
    now = datetime.now(gmt7)
    first = context.args[0].lower()
    message = ""
    remind_time_local = None

    if first == "daily":
        recurrence = "daily"
        remind_time_local = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        message = ' '.join(context.args[1:])

    elif first == "weekly":
        if len(context.args) < 3:
            await update.message.reply_text("Usage: /remind weekly <weekday> <message>")
            return
        weekday = context.args[1].lower()
        if weekday not in WEEKDAYS:
            await update.message.reply_text("❌ Invalid weekday. Use Monday-Sunday.")
            return
        recurrence = "weekly"
        message = ' '.join(context.args[2:])
        target_day = WEEKDAYS[weekday]
        days_ahead = (target_day - now.weekday() + 7) % 7 or 7
        remind_time_local = now + timedelta(days=days_ahead)
        remind_time_local = remind_time_local.replace(hour=0, minute=0, second=0, microsecond=0)

    elif first == "monthly":
        if len(context.args) < 3 or not context.args[1].isdigit():
            await update.message.reply_text("Usage: /remind monthly <day> <message>")
            return
        recurrence = "monthly"
        day = int(context.args[1])
        message = ' '.join(context.args[2:])
        year, month = now.year, now.month
        if now.day >= day:
            month += 1
            if month > 12:
                year += 1
                month = 1
        try:
            remind_time_local = gmt7.localize(datetime(year, month, day, 0, 0))
        except: return await update.message.reply_text("Invalid day of month.")

    elif first == "yearly":
        if len(context.args) < 4:
            return await update.message.reply_text("Usage: /remind yearly <day> <month> <message>")
        day = int(context.args[1])
        month_name = context.args[2].title()
        message = ' '.join(context.args[3:])
        try:
            month = datetime.strptime(month_name[:3], "%b").month
        except: return await update.message.reply_text("Invalid month.")
        recurrence = "yearly"
        year = now.year
        proposed = datetime(year, month, day, 0, 0)
        if gmt7.localize(proposed) < now:
            year += 1
        remind_time_local = gmt7.localize(datetime(year, month, day, 0, 0))

    else:
        user_tz = pytz.timezone(get_user_timezone(user_id))
        remind_time_local = parse_flexible_time(first, datetime.now(user_tz))
        if not remind_time_local:
            await update.message.reply_text("❌ Invalid format. Try: `10mins`, `10days`")
            return
        message = ' '.join(context.args[1:])

    remind_time_utc = remind_time_local.astimezone(pytz.UTC)
    add_reminder(chat_id, user_id, message, remind_time_utc, recurrence)

    await update.message.reply_text(
        f"✅ Reminder set for {remind_time_local.strftime('%Y-%m-%d %H:%M')} (Asia/Jakarta)\nRecurrence: `{recurrence}`",
        parse_mode="MarkdownV2"
    )

async def remind_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_reminders(update, context, page=1)

async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    user_id = update.effective_user.id
    tz_str = get_user_timezone(user_id)
    tz = pytz.timezone(tz_str)
    reminders = get_reminders_by_chat(update.effective_chat.id)
    if not reminders:
        await update.message.reply_text("No reminders set.")
        return

    total = len(reminders)
    per_page = 5
    pages = math.ceil(total / per_page)
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    end = start + per_page
    chunk = reminders[start:end]

    offset = tz.utcoffset(datetime.now()).total_seconds() / 3600
    tz_display = f"GMT{'+' if offset >= 0 else ''}{int(offset)}"
    msg = f"📋 *Reminders List*\nTimezone: `{tz_display}` ({tz_str})\n\n"

    for r in chunk:
        utc_time = r['run_at'].replace(tzinfo=pytz.UTC)
        local = utc_time.astimezone(tz)
        safe_text = escape_markdown(r['remind_text'], version=2)
        msg += f"🆔 `{r['id']}` | 🕒 *{local.strftime('%Y-%m-%d %H:%M')}* | 🔁 {r['recurrence']}\n📌 {safe_text}\n\n"


    buttons = [
        InlineKeyboardButton("⏪", callback_data="remindlist_1"),
        InlineKeyboardButton("⬅️", callback_data=f"remindlist_{page-1 if page > 1 else 1}"),
        InlineKeyboardButton(f"{page}/{pages}", callback_data="noop"),
        InlineKeyboardButton("➡️", callback_data=f"remindlist_{page+1 if page < pages else pages}"),
        InlineKeyboardButton("⏩", callback_data=f"remindlist_{pages}")
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([buttons]),
            parse_mode="MarkdownV2"
        )
    else:
        await update.effective_message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup([buttons]),
            parse_mode="MarkdownV2"
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.callback_query or not update.callback_query.data:
        return
    data = update.callback_query.data
    if data.startswith("remindlist_"):
        await update.callback_query.answer()
        page = int(data.split("_")[1])
        await show_reminders(update, context, page)
    elif data == "noop":
        await update.callback_query.answer()

async def remind_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command in groups.")
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /remind_delete <reminder_id>")
        return

    reminder_id = int(context.args[0])
    chat_id = update.effective_chat.id
    success = delete_reminder_by_id(reminder_id, chat_id)

    if success:
        await update.message.reply_text(f"✅ Reminder `{reminder_id}` deleted.", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ Reminder not found or doesn't belong to this chat.")

def get_handlers():
    return [
        CommandHandler("remind", remind_command),
        CommandHandler("reminder_list", remind_list),
        CommandHandler("reminder_delete", remind_delete),
        CallbackQueryHandler(handle_callback)
    ]
