import os
import asyncio
import json
from pathlib import Path
from telegram import Update, InputMediaPhoto
from telegram.constants import ChatAction
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from downloader.youtube import download_youtube, get_available_qualities, is_shorts
from downloader.tiktok import download_tiktok
from downloader.instagram import download_instagram
from downloader.x import download_x
from senders.video_sender import send_video_file
from senders.photo_sender import send_photo_file
from config import BOT_TOKEN

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

user_languages = {}  # chat_id -> lang_code
user_sessions = {}   # chat_id -> {await_quality, qualities, url}
video_cache = {}     # url -> (type, file_id)


def t(key: str, chat_id: int = None, **kwargs):
    lang = user_languages.get(chat_id, DEFAULT_LANG) if chat_id else DEFAULT_LANG
    template = LANG_DATA.get(lang, {}).get(key) or LANG_DATA[DEFAULT_LANG].get(key, key)
    return template.format(**kwargs)


# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("ask_url", chat_id=update.effective_chat.id))


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


# --- Main Handler ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    # Cek apakah user sedang memilih kualitas
    if chat_id in user_sessions and user_sessions[chat_id].get("await_quality"):
        qualities = user_sessions[chat_id]["qualities"]
        url_session = user_sessions[chat_id]["url"]
        choice = url.lower()

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(qualities):
                format_id = qualities[idx][1]
            else:
                await update.message.reply_text(t("invalid_choice_number", chat_id=chat_id))
                return
        else:
            matched = [f[1] for f in qualities if f[0].lower() == choice]
            if matched:
                format_id = matched[0]
            else:
                await update.message.reply_text(t("invalid_choice_quality", chat_id=chat_id))
                return

        await update.message.reply_text(t("start_download_quality", chat_id=chat_id, choice=choice))
        user_sessions.pop(chat_id)

        video_path = download_youtube(url_session, format_id=format_id, context=context, message=update.message)
        await send_video_file(update, context, video_path, url_session)
        return

    # Cek cache
    if url in video_cache:
        file_id = video_cache[url]
        capt = "Downloaded By @FreeVideoDownloderBot"
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        try:
            media_type, fid = file_id
            if media_type == "video":
                await context.bot.send_video(chat_id=chat_id, video=fid, caption=capt)
            elif media_type == "photo":
                await context.bot.send_photo(chat_id=chat_id, photo=fid, caption=capt)
            else:
                await context.bot.send_document(chat_id=chat_id, document=fid, caption=capt)
        except Exception as e:
            print("Error kirim cached file:", e)
            video_cache.pop(url, None)
            await update.message.reply_text(t("download_failed", chat_id=chat_id))
        return
    
    # X (Twitter)
    if "twitter.com" in url or "x.com" in url:
        await update.message.reply_text(t("x_media_detected", chat_id=chat_id))
        try:
            media_type, result = await asyncio.to_thread(download_x, url)
        except Exception as e:
            print("Download X error:", e)
            await update.message.reply_text(t("x_download_error", chat_id=chat_id))
            return

        if media_type == "video":
            await send_video_file(update, context, result, url)
        elif media_type == "photo":
            await send_photo_file(update, context, result, url)
        else:
            # fallback kirim sebagai dokumen jika format gak dikenali
            await context.bot.send_document(chat_id=chat_id, document=open(result, "rb"))
        return

    # TikTok
    if "tiktok.com" in url:
        await update.message.reply_text(t("tiktok_media_detected", chat_id=chat_id))
        try:
            media_type, result = await asyncio.to_thread(download_tiktok, url)
        except Exception as e:
            print("Download TikTok error:", e)
            await update.message.reply_text(t("tiktok_download_error", chat_id=chat_id))
            return
        if media_type == "video":
            await send_video_file(update, context, result, url)
        else:
            await update.message.reply_text(t("tiktok_failed", chat_id=chat_id))
        return

    # Instagram
    if "instagram.com" in url:
        await update.message.reply_text(t("instagram_detected", chat_id=chat_id))
        file_paths = await asyncio.to_thread(download_instagram, url)

        if not file_paths:
            await update.message.reply_text(t("download_failed", chat_id=chat_id))
            return

        # Filter hanya gambar
        image_paths = [f for f in file_paths if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        video_paths = [f for f in file_paths if f.lower().endswith(".mp4")]

        # Kirim video jika ada
        if video_paths:
            for path in video_paths:
                await send_video_file(update, context, path, url=None)

        # Kirim foto (jika lebih dari satu, kirim sebagai album)
        if image_paths:
            image_paths.sort(key=lambda x: os.path.getctime(x))
        
            if len(image_paths) == 1:
                await send_photo_file(update, context, image_paths[0], url=url)
            else:
                media_group = []
                for i, path in enumerate(image_paths):
                    with open(path, 'rb') as img_file:
                        if i == 0:
                            media_group.append(InputMediaPhoto(img_file, caption=t("Downloaded By @FreeVideoDownloderBot", chat_id=chat_id)))
                        else:
                            media_group.append(InputMediaPhoto(img_file))
                msgs = await update.message.reply_media_group(media=media_group)
                if url and msgs:
                    file_id = ("photo", msgs[0].photo[-1].file_id)
                    video_cache[url] = file_id
        return
    
    # YouTube
    if "youtube.com" in url or "youtu.be" in url:
        if is_shorts(url):
            await update.message.reply_text(t("youtube_shorts_detected", chat_id=chat_id))
            try:
                video_path = await asyncio.to_thread(download_youtube, url, context=context, message=update.message)
            except Exception as e:
                print("Download YouTube shorts error:", e)
                await update.message.reply_text(t("download_failed", chat_id=chat_id))
                return
            await send_video_file(update, context, video_path, url)
        else:
            qualities = await asyncio.to_thread(get_available_qualities, url)
            if not qualities:
                await update.message.reply_text(t("youtube_quality_fetch_failed", chat_id=chat_id))
                return

            user_sessions[chat_id] = {
                "await_quality": True,
                "qualities": qualities,
                "url": url,
            }

            quality_list = "\n".join([f"{i+1}. {q[0]}" for i, q in enumerate(qualities)])
            await update.message.reply_text(t("youtube_quality_selection", chat_id=chat_id, quality_list=quality_list))
        return

    await update.message.reply_text(t("ask_url", chat_id=chat_id))


# --- Entry Point ---
def main():
    request = HTTPXRequest(
        connect_timeout=10.0,
        read_timeout=600.0,
        write_timeout=600.0,
        pool_timeout=60.0,
    )

    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()

    # Conversation handler untuk /language
    language_handler = ConversationHandler(
        entry_points=[CommandHandler("language", handle_language_command)],
        states={
            LANGUAGE_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_selection)]
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(language_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
