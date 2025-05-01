from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *TakoNautBot*!\n\n"
        "💱 *Currency Conversion:*\n"
        "`100 USD to IDR`\n"
        "`2500 JPY to EUR`\n\n"
        "📏 *Unit Conversion:*\n"
        "`170 cm to ft`\n"
        "`25 c to f`\n\n"
        "🈳 *Text Translation:*\n"
        "Reply to any message:\n"
        "`/tl en` (Translate to English)\n\n"
        "🖼️ *Image Translation:*\n"
        "Reply to an image:\n"
        "`/tlpic <image_lang> <target_lang>`\n"
        "Example: `/tlpic ja en`\n\n"
        "Use `/help` for details.\n",
        parse_mode="Markdown"
    )