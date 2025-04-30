from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from PIL import Image
import pytesseract
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

# Mapping for user-friendly OCR language inputs to Tesseract language codes
TESSERACT_LANG_MAP = {
    'EN': 'eng', 'ENG': 'eng',
    'JP': 'jpn', 'JA': 'jpn',
    'KR': 'kor',
    'CN': 'chi_sim', 'ZH': 'chi_sim',
    'TW': 'chi_tra',
    'ID': 'ind',
    'DE': 'deu', 'FR': 'fra', 'ES': 'spa', 'IT': 'ita'
}

async def translate_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    translator = deepl.Translator(os.getenv("DEEPL_API_KEY"))

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to an image with /tlpic <image_lang> <target_lang>")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /tlpic <image_lang> <target_lang> (e.g. /tlpic jpn en)")
        return

    image_lang_input = context.args[0].upper()
    image_lang_code = TESSERACT_LANG_MAP.get(image_lang_input, image_lang_input.lower())

    target_lang_input = context.args[1].upper()
    target_lang = LANGUAGE_MAP.get(target_lang_input)

    if not target_lang:
        await update.message.reply_text(f"Unsupported target language: {target_lang_input}")
        return

    reply = update.message.reply_to_message
    photo = reply.photo
    document = reply.document

    try:
        if photo or (document and document.mime_type.startswith("image/")):
            file = await context.bot.get_file(photo[-1].file_id if photo else document.file_id)
            img_path = f"temp_{update.message.message_id}.jpg"
            await file.download_to_drive(img_path)

            text = pytesseract.image_to_string(Image.open(img_path), lang=image_lang_code)
            os.remove(img_path)

            if not text.strip():
                await update.message.reply_text("No readable text found in the image.")
                return

            result = translator.translate_text(text, target_lang=target_lang)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=result.text,
                parse_mode="Markdown",
                message_thread_id=update.message.message_thread_id,
                reply_to_message_id=update.message.message_id
            )
        else:
            await update.message.reply_text("You must reply to an image (photo or image document).")

    except Exception as e:
        await update.message.reply_text("An error occurred while translating the image.")
        print("Image translation error:", e)

def get_handler():
    return CommandHandler("tlpic", translate_picture)