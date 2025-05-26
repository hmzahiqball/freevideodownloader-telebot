import os
import json
from telegram import Update
from telegram.ext import (ContextTypes, ConversationHandler)

# --- Setup ---
os.makedirs("downloads", exist_ok=True)

with open("lang.json", "r", encoding="utf-8") as f:
    LANG_DATA = json.load(f)

DEFAULT_LANG = "en"
LANGUAGE_CHOICE = 1
AVAILABLE_LANGUAGES = {
    "English": "en",
    "Indonesia": "id",
    "Español": "es",
    "Français": "fr",
    "Germany": "de",
    "Portuguese": "pt",
    "Russian": "ru",
    "Korean": "ko",
    "Chinese": "zh",
    "Japanese": "ja",
    "Arabic": "ar"
}
user_languages = {}
user_sessions = {}
video_cache = {}
audio_cache = {}


def t(key: str, chat_id: int = None, **kwargs):
    lang = user_languages.get(chat_id, DEFAULT_LANG) if chat_id else DEFAULT_LANG
    template = LANG_DATA.get(lang, {}).get(key) or LANG_DATA[DEFAULT_LANG].get(key, key)
    return template.format(**kwargs)


# Saat user mengetik /language
async def handle_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    language_list = "\n".join([f"{i+1}. {lang}" for i, lang in enumerate(AVAILABLE_LANGUAGES.keys())])
    await update.message.reply_text(f"Choose language:\n{language_list}")
    return LANGUAGE_CHOICE


# Setelah user memilih angka bahasa
async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()

    if not user_input.isdigit():
        await update.message.reply_text(t("language_usage", chat_id))
        return ConversationHandler.END

    idx = int(user_input) - 1
    if idx < 0 or idx >= len(AVAILABLE_LANGUAGES):
        await update.message.reply_text(t("language_usage", chat_id))
        return ConversationHandler.END

    lang_name = list(AVAILABLE_LANGUAGES.keys())[idx]
    lang_code = AVAILABLE_LANGUAGES[lang_name]
    user_languages[chat_id] = lang_code

    await update.message.reply_text(t("language_set", chat_id, lang=lang_name))
    return ConversationHandler.END

