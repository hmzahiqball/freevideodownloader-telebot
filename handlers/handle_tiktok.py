import asyncio
import json
from telegram.constants import ChatAction
from downloader.tiktok import download_tiktok
from senders.video_sender import send_video_file

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

user_languages = {}  # chat_id -> lang_code
video_cache = {}     # url -> (type, file_id) or special keys for media groups

def t(key: str, chat_id: int = None, **kwargs):
    lang = user_languages.get(chat_id, DEFAULT_LANG) if chat_id else DEFAULT_LANG
    template = LANG_DATA.get(lang, {}).get(key) or LANG_DATA[DEFAULT_LANG].get(key, key)
    return template.format(**kwargs)

async def handle_tiktok(update, context, url, capt):
    # Check cache
    chat_id = update.effective_chat.id
    if url in video_cache:
        media_type, file_id = video_cache[url]
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        await context.bot.send_video(chat_id=chat_id, video=file_id, caption=capt)
        print("TikTok sent from cache.")
        return
        
    await update.message.reply_text(t("tiktok_media_detected", chat_id=chat_id))
    try:
        media_type, result = await asyncio.to_thread(download_tiktok, url)
    except Exception as e:
        print("Download TikTok error:", e)
        await update.message.reply_text(t("tiktok_download_error", chat_id=chat_id))
        return
    if media_type == "video":
        await send_video_file(update, context, result, url, video_cache=video_cache, t=t)
    else:
        await update.message.reply_text(t("tiktok_failed", chat_id=chat_id))
    return