from telegram import Update
from telegram.ext import ContextTypes
from utils import parse_message, convert_currency, format_rate

async def handle_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    time_str = timestamp[:16].replace("T", " ") + " UTC"
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