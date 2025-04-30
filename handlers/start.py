from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to TakoNautBot!\n\n"
        "Try:\n"
        "`100 USD to IDR`\n"
        "`170 cm to ft`\n"
        "`25 c to f`\n"
        "Supports currencies 💱 and units 📏\n",
        parse_mode="Markdown"
    )