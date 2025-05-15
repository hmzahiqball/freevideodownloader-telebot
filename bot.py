import os
import asyncio
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
from downloader.tiktok import download_tiktok, download_tiktok_photo_gallery
from downloader.instagram import download_instagram
from config import BOT_TOKEN

os.makedirs("downloads", exist_ok=True)

# Simpan sesi user yang menunggu input kualitas video
user_sessions = {}

# Cache file_id video untuk menghindari upload ulang
video_cache = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Silahkan kirimkan URL video yang akan didownload")

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
                await update.message.reply_text("Pilihan tidak valid, silahkan kirim nomor yang sesuai.")
                return
        else:
            matched = [f[1] for f in qualities if f[0].lower() == choice]
            if matched:
                format_id = matched[0]
            else:
                await update.message.reply_text("Pilihan tidak valid, silahkan kirim nomor atau kualitas yang sesuai.")
                return

        await update.message.reply_text(f"Mulai mengunduh video dengan kualitas {choice} ...")
        user_sessions.pop(chat_id)

        video_path = download_youtube(url_session, format_id=format_id, context=context, message=update.message)
        print(f"Download complete: {video_path}")
        await send_video_file(update, context, video_path, url_session)
        return

    # Cek cache
    if url in video_cache:
        capt = "Downloaded By @FreeVideoDownloderBot"
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        await context.bot.send_video(chat_id=chat_id, video=video_cache[url], caption=capt)
        return

    # TikTok
    if "tiktok.com" in url:
        if "/photo/" in url:
            # Proses khusus galeri foto/slideshow TikTok
            await update.message.reply_text("📷 Terdeteksi galeri foto TikTok, sedang mengunduh gambar...")

            # Implementasi khusus untuk galeri foto (misal scrape manual atau API lain)
            images = await download_tiktok_photo_gallery(url)
            if not images:
                await update.message.reply_text("❌ Gagal mengunduh foto dari galeri TikTok.")
                return

            for img_path in images:
                await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
                with open(img_path, "rb") as f:
                    await context.bot.send_photo(chat_id=chat_id, photo=f)
                os.remove(img_path)
            print("Download complete: TikTok photo gallery")
            return

        else:
            # Proses unduh video TikTok biasa pakai yt-dlp
            await context.bot.send_message(chat_id=chat_id, text="🔄 TikTok media terdeteksi, sedang mengunduh...")
            try:
                media_type, result = await asyncio.to_thread(download_tiktok, url)
            except Exception as e:
                print("Error saat download_tiktok:", e)
                await context.bot.send_message(chat_id=chat_id, text=f"❌ Terjadi error saat mengunduh TikTok: {e}")
                return

        if media_type == "video":
            await send_video_file(update, context, result, url=url)
        elif media_type == "images":
            await update.message.reply_text("📷 Slideshow terdeteksi, mengirim foto satu per satu...")
            for img_path in result:
                await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
                with open(img_path, 'rb') as img:
                    await context.bot.send_photo(chat_id=chat_id, photo=img)
                os.remove(img_path)
            print("Download complete: TikTok slideshow")
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Gagal mengunduh dari TikTok.")
        return

    # Instagram
    if "instagram.com" in url:
        await context.bot.send_message(chat_id=chat_id, text="🔄 Instagram terdeteksi, sedang mengunduh...")
        video_path = download_instagram(url)
        print(f"Download complete: {video_path}")
        await send_video_file(update, context, video_path, url)
        return

    # YouTube
    if "youtube.com" in url or "youtu.be" in url:
        if is_shorts(url):
            await context.bot.send_message(chat_id=chat_id, text="🔄 YouTube Shorts terdeteksi, langsung mengunduh video...")
            video_path = download_youtube(url, context=context, message=update.message)
            print(f"Download complete: {video_path}")
            await send_video_file(update, context, video_path, url)
        else:
            qualities = get_available_qualities(url)
            if not qualities:
                await context.bot.send_message(chat_id=chat_id, text="❌ Tidak bisa mengambil daftar kualitas dari video.")
                return
        
            # Simpan sesi agar user bisa memilih
            user_sessions[chat_id] = {
                "await_quality": True,
                "qualities": qualities,
                "url": url,
            }
        
            quality_list = "\n".join([f"{i+1}. {q[0]}" for i, q in enumerate(qualities)])
            await context.bot.send_message(chat_id=chat_id, text=f"📺 Video YouTube terdeteksi.\nPilih kualitas yang diinginkan:\n\n{quality_list}\n\nKirim nomor atau teks (misal: 1 atau 360p)")
        return

    await update.message.reply_text("Silahkan kirimkan URL video yang akan didownload")

async def send_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: str, url: str = None):
    chat_id = update.effective_chat.id
    capt = "Downloaded By @FreeVideoDownloderBot"

    if not video_path:
        await context.bot.send_message(chat_id=chat_id, text="❌ Gagal mengunduh video.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

    video_sent = False
    try:
        file_size = os.path.getsize(video_path)
        with open(video_path, "rb") as f:
            if file_size <= 20 * 1024 * 1024:
                msg = await context.bot.send_video(
                    chat_id=chat_id,
                    video=f,
                    caption=capt
                )
                if url:
                    video_cache[url] = msg.video.file_id
            else:
                msg = await context.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    caption=capt
                )
                if url and msg.document:
                    video_cache[url] = msg.document.file_id
        video_sent = True
    except asyncio.TimeoutError:
        print("Telegram send timeout")
    except Exception as e:
        print("Telegram send error:", e)
        await asyncio.sleep(5)
        if not video_sent:
            await context.bot.send_message(chat_id=chat_id, text="❌ Gagal mengirim video.")
    finally:
        os.remove(video_path)
        print("Video Sent!")

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

