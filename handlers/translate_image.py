from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from PIL import Image
import pytesseract
import os
from google.cloud import translate_v2 as translate

# Manual mapping for language aliases to Google Translate codes
LANGUAGE_MAP = {
    'EN': 'en', 'EN-US': 'en', 'EN-GB': 'en',
    'JP': 'ja', 'JA': 'ja',
    'CN': 'zh', 'ZH': 'zh',
    'KR': 'ko', 'KO': 'ko',
    'ID': 'id', 'FR': 'fr', 'DE': 'de', 'ES': 'es', 'IT': 'it',
    'NL': 'nl', 'PL': 'pl', 'PT': 'pt', 'RU': 'ru', 'UK': 'uk'
}

# Mapping for user-friendly OCR language inputs to Tesseract language codes
TESSERACT_LANG_MAP = {
    'EN': 'eng', 'ENG': 'eng',
    'JP': 'jpn', 'JA': 'jpn',
    'KR': 'kor',
    'CN': 'chi_sim', 'ZH': 'chi_sim',
    'TW': 'chi_tra',
    'ID': 'ind',
    'DE': 'deu', 'FR': 'fra', 'ES': 'spa', 'IT': 'ita', 'HI': 'hin'
}

async def translate_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = translate.Client()

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to an image with /tlpic <image_lang> <target_lang>")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /tlpic <image_lang> <target_lang> (e.g. /tlpic jpn en)")
        return

    image_lang_input = context.args[0].strip()
    image_lang_code = TESSERACT_LANG_MAP.get(image_lang_input.upper(), image_lang_input.lower())

    target_lang_input = context.args[1].strip()
    target_lang = LANGUAGE_MAP.get(target_lang_input.upper(), target_lang_input.lower())

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

            result = client.translate(text, target_language=target_lang)
            translated_text = result['translatedText']

            send_kwargs = {
                "chat_id": update.effective_chat.id,
                "text": translated_text,
                "parse_mode": "Markdown",
                "reply_to_message_id": update.message.message_id
            }

            # ✅ Use thread ID from the replied-to message (to avoid General-topic error)
            if hasattr(reply, "message_thread_id") and reply.message_thread_id:
                send_kwargs["message_thread_id"] = reply.message_thread_id

            await context.bot.send_message(**send_kwargs)
        else:
            await update.message.reply_text("You must reply to an image (photo or image document).")

    except Exception as e:
        await update.message.reply_text("An error occurred while translating the image.")
        print("Image translation error:", e)

def get_handler():
    return CommandHandler("tlpic", translate_picture)
