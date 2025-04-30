from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import deepl
import os

# Manual mapping for language aliases to DeepL codes
LANGUAGE_MAP = {
    'EN': 'EN-US', 'EN-US': 'EN-US', 'EN-GB': 'EN-GB',
    'JP': 'JA', 'JA': 'JA',
    'CN': 'ZH', 'ZH': 'ZH',
    'KR': 'KO', 'KO': 'KO',
    'ID': 'ID',
    'FR': 'FR', 'DE': 'DE', 'ES': 'ES', 'IT': 'IT',
    'NL': 'NL', 'PL': 'PL', 'PT': 'PT-PT', 'RU': 'RU',
    'UK': 'UK'
}

async def translate_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    translator = deepl.Translator(os.getenv("DEEPL_API_KEY"))

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a text message with /tl <LANGCODE>, e.g. /tl EN")
        return

    # Determine language
    if context.args:
        lang_input = context.args[0].upper()
        lang = LANGUAGE_MAP.get(lang_input)
        if not lang:
            await update.message.reply_text(f"Unsupported language code: {lang_input}")
            return
    else:
        lang = 'EN-US'

    reply = update.message.reply_to_message

    try:
        if reply.text:
            text = reply.text
        else:
            await update.message.reply_text("Reply must be a text message.")
            return

        # Translate with DeepL SDK
        result = translator.translate_text(text, target_lang=lang)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result.text,
            parse_mode="Markdown",
            message_thread_id=update.message.message_thread_id,
            reply_to_message_id=update.message.message_id
        )

    except Exception as e:
        await update.message.reply_text("Failed to process translation.")
        print("Translation error:", e)

def get_handler():
    return CommandHandler("tl", translate_content)