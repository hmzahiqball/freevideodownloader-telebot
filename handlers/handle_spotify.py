import os
import asyncio
import shutil
from pathlib import Path
from downloader.spotify import download_spotify
from state import t, audio_cache

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

async def handle_spotify(update, context, url, capt):
    chat_id = update.effective_chat.id

    # Cek dulu apakah audio udah ada di cache memory (file_id Telegram)
    if url in audio_cache:
        media_type, file_id = audio_cache[url]
        if media_type == "audio":
            await context.bot.send_chat_action(chat_id=chat_id, action="upload_audio")
            await context.bot.send_audio(chat_id=chat_id, audio=file_id, caption=capt)
            print("Spotify sent from Telegram cache (file_id).")
            return

    # Kalau belum ada cache, proses download dan simpan cache baru
    await update.message.reply_text(t("spotify_detected", chat_id=chat_id))

    try:
        media_type, result = await asyncio.to_thread(download_spotify, url)
    except Exception as e:
        print("Download Spotify error:", e)
        await update.message.reply_text(t("spotify_download_error", chat_id=chat_id))
        return

    if media_type == "audio":
        folder_path = Path(result)
        audio_path = next((p for p in folder_path.iterdir() if p.suffix == ".mp3"), None)
        if audio_path:
            try:
                with open(audio_path, "rb") as audio_file:
                    sent_msg = await context.bot.send_audio(chat_id=chat_id, audio=audio_file, caption=capt)

                # Simpan file_id ke cache supaya next time bisa pakai langsung
                audio_cache[url] = ("audio", sent_msg.audio.file_id)

                # Hapus folder download setelah sukses
                shutil.rmtree(folder_path)
                print("Spotify downloaded, sent, and cache saved (file_id).")

            except Exception as e:
                print("Send Spotify audio error:", e)
                await update.message.reply_text(t("spotify_failed", chat_id=chat_id))
        else:
            print("No audio file found in downloaded folder.")
            await update.message.reply_text(t("spotify_failed", chat_id=chat_id))
    else:
        print("Download result is not audio.")
        await update.message.reply_text(t("spotify_failed", chat_id=chat_id))
