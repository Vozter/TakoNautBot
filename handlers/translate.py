from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from google.cloud import translate_v2 as translate

# Manual mapping for language aliases to Google Translate codes
LANGUAGE_MAP = {
    'EN': 'en', 'EN-US': 'en', 'EN-GB': 'en',
    'JP': 'ja', 'JA': 'ja',
    'CN': 'zh', 'ZH': 'zh',
    'KR': 'ko', 'KO': 'ko',
    'ID': 'id',
    'FR': 'fr', 'DE': 'de', 'ES': 'es', 'IT': 'it',
    'NL': 'nl', 'PL': 'pl', 'PT': 'pt', 'RU': 'ru',
    'UK': 'uk'
}

async def translate_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = translate.Client()

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a text message with /tl <LANGCODE>, e.g. /tl EN")
        return


    # Determine language
    if context.args:
        lang_input = context.args[0].strip()
        # Use alias from map if found, otherwise use the raw code (in lowercase)
        lang = LANGUAGE_MAP.get(lang_input.upper(), lang_input.lower())
    else:
        lang = 'en'

    reply = update.message.reply_to_message

    try:
        if reply.text:
            text = reply.text
        else:
            await update.message.reply_text("Reply must be a text message.")
            return

        # Translate with Google Translate API
        result = client.translate(text, target_language=lang)
        translated_text = result['translatedText']

        send_kwargs = {
            "chat_id": update.effective_chat.id,
            "text": translated_text,
            "parse_mode": "Markdown",
            "reply_to_message_id": update.message.message_id
        }

        # ✅ Use thread ID from the replied-to message (safer than the command)
        if hasattr(update.message.reply_to_message, "message_thread_id"):
            thread_id = update.message.reply_to_message.message_thread_id
            if thread_id is not None:
                send_kwargs["message_thread_id"] = thread_id

        await context.bot.send_message(**send_kwargs)

    except Exception as e:
        await update.message.reply_text("Failed to process translation.")
        print("Translation error:", e)

def get_handler():
    return CommandHandler("tl", translate_content)
