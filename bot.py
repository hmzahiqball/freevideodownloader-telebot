import os
import asyncio
import json
from telegram import Update
from telegram.constants import ChatAction
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from downloader.youtube import download_youtube, get_available_qualities, is_shorts
from downloader.tiktok import download_tiktok
from downloader.instagram import download_instagram
from config import BOT_TOKEN

os.makedirs("downloads", exist_ok=True)

# Load bahasa
with open("lang.json", "r", encoding="utf-8") as f:
    LANG_DATA = json.load(f)

DEFAULT_LANG = "en"

def t(key: str, lang: str = DEFAULT_LANG, **kwargs):
    template = LANG_DATA.get(lang, {}).get(key) or LANG_DATA[DEFAULT_LANG].get(key, key)
    return template.format(**kwargs)

# Simpan sesi user yang menunggu input kualitas video
user_sessions = {}

# Cache file_id video untuk menghindari upload ulang
video_cache = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("ask_url"))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    # Jika user sedang memilih kualitas
    if chat_id in user_sessions and user_sessions[chat_id].get("await_quality"):
        qualities = user_sessions[chat_id]["qualities"]
        url_session = user_sessions[chat_id]["url"]
        choice = url.lower()

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(qualities):
                format_id = qualities[idx][1]
            else:
                await update.message.reply_text(t("invalid_choice_number"))
                return
        else:
            matched = [f[1] for f in qualities if f[0].lower() == choice]
            if matched:
                format_id = matched[0]
            else:
                await update.message.reply_text(t("invalid_choice_quality"))
                return

        await update.message.reply_text(t("start_download_quality", choice=choice))
        user_sessions.pop(chat_id)

        video_path = download_youtube(url_session, format_id=format_id, context=context, message=update.message)
        print(f"Download complete: {video_path}")
        await send_video_file(update, context, video_path, url_session)
        return

    # Jika URL ada di cache, langsung kirim file cached
    if url in video_cache:
        file_id = video_cache[url]
        capt = "Downloaded By @FreeVideoDownloderBot"
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        try:
            if isinstance(file_id, tuple):
                # Kalau cache simpan (type, file_id)
                media_type, fileid = file_id
                if media_type == "video":
                    await context.bot.send_video(chat_id=chat_id, video=fileid, caption=capt)
                else:
                    await context.bot.send_document(chat_id=chat_id, document=fileid, caption=capt)
            else:
                # Cache lama, asumsi video
                await context.bot.send_video(chat_id=chat_id, video=file_id, caption=capt)
        except Exception as e:
            print("Error kirim cached file_id:", e)
            # Jika error, hapus cache biar retry download di lain waktu
            video_cache.pop(url, None)
            await update.message.reply_text(t("download_failed"))
        else:
            print("Video sent from cache.")
        return

    # TikTok
    if "tiktok.com" in url:
        await context.bot.send_message(chat_id=chat_id, text=t("tiktok_media_detected"))
        try:
            media_type, result = await asyncio.to_thread(download_tiktok, url)
            print(f"Download complete: {result}")
        except Exception as e:
            print("Error saat download_tiktok:", e)
            await context.bot.send_message(chat_id=chat_id, text=t("tiktok_download_error"))
            return

        if media_type == "video":
            await send_video_file(update, context, result, url=url)
        else:
            await context.bot.send_message(chat_id=chat_id, text=t("tiktok_failed"))
        return

    # Instagram
    if "instagram.com" in url:
        await context.bot.send_message(chat_id=chat_id, text=t("instagram_detected"))
        video_path = download_instagram(url)
        print(f"Download complete: {video_path}")
        await send_video_file(update, context, video_path, url)
        return

    # YouTube
    if "youtube.com" in url or "youtu.be" in url:
        if is_shorts(url):
            await context.bot.send_message(chat_id=chat_id, text=t("youtube_shorts_detected"))
            video_path = download_youtube(url, context=context, message=update.message)
            print(f"Download complete: {video_path}")
            await send_video_file(update, context, video_path, url)
        else:
            qualities = get_available_qualities(url)
            if not qualities:
                await context.bot.send_message(chat_id=chat_id, text=t("youtube_quality_fetch_failed"))
                return
        
            # Simpan sesi agar user bisa memilih
            user_sessions[chat_id] = {
                "await_quality": True,
                "qualities": qualities,
                "url": url,
            }
        
            quality_list = "\n".join([f"{i+1}. {q[0]}" for i, q in enumerate(qualities)])
            await context.bot.send_message(chat_id=chat_id, text=t("youtube_quality_selection", quality_list=quality_list))
        return

    await update.message.reply_text(t("ask_url"))

async def send_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: str, url: str = None):
    chat_id = update.effective_chat.id
    capt = "Downloaded By @FreeVideoDownloderBot"

    if not video_path or not os.path.exists(video_path):
        await context.bot.send_message(chat_id=chat_id, text=t("download_failed"))
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

    file_size = os.path.getsize(video_path)

    with open(video_path, "rb") as f:
        try:
            if file_size <= 20 * 1024 * 1024:
                msg = await context.bot.send_video(chat_id=chat_id, video=f, caption=capt)
                media_type = "video"
            else:
                msg = await context.bot.send_document(chat_id=chat_id, document=f, caption=capt)
                media_type = "document"
        except asyncio.TimeoutError:
            print("Telegram send timeout, retrying after 5 seconds...")
            await asyncio.sleep(5)
            return await send_video_file(update, context, video_path, url)
        except Exception as e:
            print("Telegram send error:", e)
            # Jangan kirim pesan timedout, tapi beri tahu gagal
            await context.bot.send_message(chat_id=chat_id, text=t("send_failed"))
            return

    # Cache file_id Telegram supaya cepat kirim ulang di masa depan
    if url and msg and (msg.video or msg.document):
        file_id = (media_type, (msg.video or msg.document).file_id)
        video_cache[url] = file_id

    try:
        os.remove(video_path)
    except Exception as e:
        print("Failed to remove file:", e)

    print("Video sent successfully!")

def main():
    request = HTTPXRequest(
        connect_timeout=10.0,
        read_timeout=600.0,
        write_timeout=600.0,
        pool_timeout=60.0,
    )

    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

