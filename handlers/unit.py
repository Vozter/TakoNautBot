from telegram import Update
from telegram.ext import ContextTypes
from utils import parse_unit_message, convert_unit, format_rate

async def handle_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parsed = parse_unit_message(update.message.text)
    if not parsed:
        return

    amount, from_unit, to_unit = parsed
    result, conversion_rate = convert_unit(amount, from_unit, to_unit)

    if result is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Unsupported unit. Try using 'kg', 'cm', 'mile', etc. Or try again later.",
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
