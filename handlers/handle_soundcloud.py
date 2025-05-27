# handlers/soundcloud_handler.py
import asyncio
import os
from telegram.constants import ChatAction
from downloader.soundcloud import download_soundcloud
from state import t, video_cache

async def handle_soundcloud(update, context, url, capt=""):
    chat_id = update.effective_chat.id

    # Cek cache dulu
    if url in video_cache:
        media_type, file_id = video_cache[url]
        if media_type == "audio":
            print(f"SoundCloud: Sent from cache")
            await context.bot.send_chat_action(chat_id=chat_id, action="upload_audio")
            await context.bot.send_audio(chat_id=chat_id, audio=file_id, caption=capt if capt else "🎵 SoundCloud Audio")
            return

    await update.message.reply_text(t("soundcloud_detected", chat_id=chat_id))
    await context.bot.send_chat_action(chat_id=chat_id, action="upload_audio")

    try:
        path, title = await asyncio.to_thread(download_soundcloud, url)
        caption = capt if capt else f"🎵 {title}"
        with open(path, 'rb') as f:
            msg = await context.bot.send_audio(chat_id=chat_id, audio=f, caption=caption)
            video_cache[url] = ("audio", msg.audio.file_id)
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"File downloaded removed: {path}")
        except Exception as e:
            print(f"Failed to remove file: {e}")

        print(f"SoundCloud: downloaded and sent")

    except Exception as e:
        print("Error download SoundCloud:", e)
        await update.message.reply_text(t("soundcloud_download_error", chat_id=chat_id))
