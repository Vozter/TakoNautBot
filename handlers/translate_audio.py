import os
import subprocess
import tempfile
import asyncio
import html
import re

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from google.cloud import translate_v3 as translate
from google.cloud.translate_v3 import TranslationServiceClient
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

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

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or "zeta-verbena-258608"
LOCATION = "global"

def get_handler():
    return CommandHandler("tlvoice", translate_media)

async def translate_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Detach the long-running job to run in background
    asyncio.create_task(process_translation(update, context))
    await update.message.reply_text("⏳ Processing your file... please wait.")

async def process_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not (update.message.reply_to_message.video or update.message.reply_to_message.document or update.message.reply_to_message.audio or update.message.reply_to_message.voice):
        await update.message.reply_text("Please reply to an audio or video file with /tlvoice <target_language> (e.g., /tlvoice en)")
        return

    if not context.args:
        await update.message.reply_text("Please specify target language, e.g., /tlvoice en")
        return

    lang_input = context.args[0].upper()
    target_lang = LANGUAGE_MAP.get(lang_input, lang_input.lower())

    media = (
        update.message.reply_to_message.video or
        update.message.reply_to_message.document or
        update.message.reply_to_message.audio or
        update.message.reply_to_message.voice
    )

    if media.file_size > 20 * 1024 * 1024:
        await update.message.reply_text("🚫 File too big. Please send a file under 20MB.")
        return

    file = await context.bot.get_file(media.file_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        media_path = os.path.join(tmpdir, "input")
        audio_path = os.path.join(tmpdir, "audio.mp3")

        await file.download_to_drive(media_path)

        await asyncio.get_event_loop().run_in_executor(
            None,
            subprocess.run,
            ["ffmpeg", "-y", "-i", media_path, "-vn", "-ar", "16000", "-ac", "1", audio_path],
            {"check": True}
        )

        def whisper_transcribe(path):
            with open(path, "rb") as audio_file:
                return openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                ).text.strip()

        full_text = await asyncio.get_event_loop().run_in_executor(None, whisper_transcribe, audio_path)

        if not full_text:
            await update.message.reply_text("No speech detected in the media.")
            return

        def format_paragraphs(text):
            sentence_endings = r'(?<=[。．？！!?\.!?])\s+'
            sentences = re.split(sentence_endings, text)
            sentences = [s.strip() for s in sentences if s.strip()]

            chunks = []
            chunk = []
            char_limit = 200

            for sentence in sentences:
                if sum(len(s) for s in chunk) + len(sentence) < char_limit:
                    chunk.append(sentence)
                else:
                    chunks.append(" ".join(chunk))
                    chunk = [sentence]
            if chunk:
                chunks.append(" ".join(chunk))

            return "\n\n".join(chunks)

        formatted_transcript = format_paragraphs(full_text)

        client = TranslationServiceClient()
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.translate_text(
                    contents=[full_text],
                    target_language_code=target_lang,
                    mime_type="text/plain",
                    parent=parent
                )
            )
            translated_text = html.unescape(response.translations[0].translated_text)
            formatted_translation = format_paragraphs(translated_text)
        except Exception as e:
            formatted_translation = "(Translation failed)"
            print("Translation error:", e)

        await update.message.reply_text(
            f"\U0001F4DD *Transcript*\n{formatted_transcript}\n\n\U0001F310 *Translated ({target_lang.upper()})*\n{formatted_translation}",
            parse_mode="Markdown"
        )
