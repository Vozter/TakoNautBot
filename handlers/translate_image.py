from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from PIL import Image, ImageEnhance
import pytesseract
import os
from google.cloud import translate_v2 as translate
import html

# Google Translate language codes (ISO 639-1)
LANGUAGE_MAP = {
    'EN': 'en', 'EN-US': 'en', 'EN-GB': 'en',
    'JP': 'ja', 'JA': 'ja',
    'CN': 'zh', 'ZH': 'zh',
    'KR': 'ko', 'KO': 'ko',
    'ID': 'id', 'FR': 'fr', 'DE': 'de', 'ES': 'es', 'IT': 'it',
    'NL': 'nl', 'PL': 'pl', 'PT': 'pt', 'RU': 'ru', 'UK': 'uk',
    'HI': 'hi'
}

# Map from Google Translate codes to Tesseract codes (ISO 639-2 or internal codes)
GOOGLE_TO_TESSERACT_LANG_MAP = {
    'af': 'afr', 'am': 'amh', 'ar': 'ara', 'az': 'aze', 'be': 'bel',
    'bg': 'bul', 'bn': 'ben', 'ca': 'cat', 'cs': 'ces', 'cy': 'cym',
    'da': 'dan', 'de': 'deu', 'el': 'ell', 'en': 'eng', 'es': 'spa',
    'et': 'est', 'fa': 'fas', 'fi': 'fin', 'fr': 'fra', 'ga': 'gle',
    'gu': 'guj', 'he': 'heb', 'hi': 'hin', 'hr': 'hrv', 'hu': 'hun',
    'hy': 'hye', 'id': 'ind', 'is': 'isl', 'it': 'ita', 'ja': 'jpn',
    'ka': 'kat', 'kk': 'kaz', 'km': 'khm', 'kn': 'kan', 'ko': 'kor',
    'lt': 'lit', 'lv': 'lav', 'ml': 'mal', 'mr': 'mar', 'ms': 'msa',
    'my': 'mya', 'ne': 'nep', 'nl': 'nld', 'no': 'nor', 'pa': 'pan',
    'pl': 'pol', 'pt': 'por', 'ro': 'ron', 'ru': 'rus', 'si': 'sin',
    'sk': 'slk', 'sl': 'slv', 'sq': 'sqi', 'sr': 'srp', 'sv': 'swe',
    'ta': 'tam', 'te': 'tel', 'th': 'tha', 'tr': 'tur', 'uk': 'ukr',
    'ur': 'urd', 'vi': 'vie', 'zh': 'chi_sim'
}

def get_google_lang_code(code: str) -> str:
    return LANGUAGE_MAP.get(code.upper(), code.lower())

def get_tesseract_lang_code(code: str) -> str:
    google_code = get_google_lang_code(code)
    return GOOGLE_TO_TESSERACT_LANG_MAP.get(google_code, 'eng')  # fallback to eng

async def translate_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client = translate.Client()

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to an image with /tlpic <image_lang> <target_lang>")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /tlpic <image_lang> <target_lang> (e.g. /tlpic hi en)")
        return

    image_lang_code = get_tesseract_lang_code(context.args[0])
    target_lang = get_google_lang_code(context.args[1])

    reply = update.message.reply_to_message
    photo = reply.photo
    document = reply.document

    try:
        if photo or (document and document.mime_type.startswith("image/")):
            file = await context.bot.get_file(photo[-1].file_id if photo else document.file_id)
            img_path = f"temp_{update.message.message_id}.jpg"
            await file.download_to_drive(img_path)

            processed_img = preprocess_image(img_path)
            text = pytesseract.image_to_string(processed_img, lang=image_lang_code)
            text = text.replace('|', '').strip()
            os.remove(img_path)

            if not text:
                await update.message.reply_text("No readable text found in the image.")
                return

            result = client.translate(text, target_language=target_lang)
            translated_text = html.unescape(result['translatedText'])

            send_kwargs = {
                "chat_id": update.effective_chat.id,
                "text": translated_text,
                "parse_mode": "Markdown",
                "reply_to_message_id": update.message.message_id
            }

            if hasattr(reply, "message_thread_id") and reply.message_thread_id:
                send_kwargs["message_thread_id"] = reply.message_thread_id

            await context.bot.send_message(**send_kwargs)
        else:
            await update.message.reply_text("You must reply to an image (photo or image document).")

    except Exception as e:
        await update.message.reply_text("An error occurred while translating the image.")
        print("Image translation error:", e)

def detect_rotation(img: Image.Image) -> Image.Image:
    try:
        osd = pytesseract.image_to_osd(img)
        angle = int([line for line in osd.split("\n") if "Rotate" in line][0].split(":")[1].strip())
        if angle != 0:
            print(f"Rotating image by {angle} degrees")
            img = img.rotate(-angle, expand=True)
    except Exception as e:
        print(f"Rotation detection failed: {e}")
    return img

def preprocess_image(img_path):
    img = Image.open(img_path).convert("L")
    img = detect_rotation(img)
    img = img.resize((1200, int(img.height * (1200 / img.width))))
    img = ImageEnhance.Sharpness(img).enhance(2.5)
    img = img.point(lambda p: 255 if p > 150 else 0)
    return img

def get_handler():
    return CommandHandler("tlpic", translate_picture)
