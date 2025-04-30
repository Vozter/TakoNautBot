from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from PIL import Image
import pytesseract
import deepl
import os

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
translator = deepl.Translator(DEEPL_API_KEY)

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
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a message or image with /tl <LANGCODE>, e.g. /tl EN")
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
    photo = reply.photo
    document = reply.document

    try:
        if photo or (document and document.mime_type.startswith("image/")):
            # Download image
            file = (await context.bot.get_file(photo[-1].file_id if photo else document.file_id))
            img_path = f"temp_{update.message.message_id}.jpg"
            await file.download_to_drive(img_path)

            # OCR
            text = pytesseract.image_to_string(Image.open(img_path))
            os.remove(img_path)

            if not text.strip():
                await update.message.reply_text("No text found in image.")
                return
        elif reply.text:
            text = reply.text
        else:
            await update.message.reply_text("Unsupported reply type. Reply to a photo or text message.")
            return

        # Translate with DeepL SDK
        result = translator.translate_text(text, target_lang=lang)
        await update.message.reply_text(f"{result.text}")

    except Exception as e:
        await update.message.reply_text("Failed to process translation.")
        print("Translation error:", e)

def get_handler():
    return CommandHandler("tl", translate_content)
