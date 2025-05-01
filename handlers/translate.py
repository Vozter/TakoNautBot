from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from google.cloud import translate_v3 as translate
from google.cloud.translate_v3 import TranslationServiceClient
import html
import os

# Manual mapping for language aliases to Google Translate codes
LANGUAGE_MAP = {
    'EN': 'en', 'EN-US': 'en', 'EN-GB': 'en',
    'JP': 'ja', 'JA': 'ja',
    'CN': 'zh', 'ZH': 'zh',
    'KR': 'ko', 'KO': 'ko',
    'ID': 'id',
    'FR': 'fr', 'DE': 'de', 'ES': 'es', 'IT': 'it',
    'NL': 'nl', 'PL': 'pl', 'PT': 'pt', 'RU': 'ru',
    'UK': 'uk', 'HI': 'hi'
}

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or "zeta-verbena-258608"  # or your actual project ID
LOCATION = "global"  # NMT default location

async def translate_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = TranslationServiceClient()
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a text message with /tl <LANGCODE>, e.g. /tl EN")
        return

    # Determine target language
    if context.args:
        lang_input = context.args[0].strip()
        target_lang = LANGUAGE_MAP.get(lang_input.upper(), lang_input.lower())
    else:
        target_lang = "en"

    reply = update.message.reply_to_message
    if not reply.text:
        await update.message.reply_text("Reply must be a text message.")
        return

    try:
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
        response = client.translate_text(
            contents=[reply.text],
            target_language_code=target_lang,
            mime_type="text/plain",
            parent=parent,
        )
        translated_text = html.unescape(response.translations[0].translated_text)

        send_kwargs = {
            "chat_id": update.effective_chat.id,
            "text": translated_text,
            "parse_mode": "Markdown",
            "reply_to_message_id": update.message.message_id
        }

        if hasattr(reply, "message_thread_id") and reply.message_thread_id:
            send_kwargs["message_thread_id"] = reply.message_thread_id

        await context.bot.send_message(**send_kwargs)

    except Exception as e:
        await update.message.reply_text("Failed to process translation.")
        print("Translation error:", e)

def get_handler():
    return CommandHandler("tl", translate_content)
