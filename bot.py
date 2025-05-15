import os
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
import asyncio

os.makedirs("downloads", exist_ok=True)

# Simpan sesi user yang menunggu input kualitas video
user_sessions = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Silahkan kirimkan URL video yang akan didownload")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    # Jika user sedang diminta pilih kualitas
    if chat_id in user_sessions and user_sessions[chat_id].get("await_quality"):
        qualities = user_sessions[chat_id]["qualities"]
        url_session = user_sessions[chat_id]["url"]

        choice = url.lower()

        # Cek input angka
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(qualities):
                format_id = qualities[idx][1]
            else:
                await update.message.reply_text("Pilihan tidak valid, silahkan kirim nomor yang sesuai.")
                return
        else:
            # Cek input label langsung (misal '720p')
            matched = [f[1] for f in qualities if f[0].lower() == choice]
            if matched:
                format_id = matched[0]
            else:
                await update.message.reply_text("Pilihan tidak valid, silahkan kirim nomor atau kualitas yang sesuai.")
                return

        await update.message.reply_text(f"Mulai mengunduh video dengan kualitas {choice} ...")
        user_sessions.pop(chat_id)  # Hapus sesi

        video_path = download_youtube(url_session, format_id=format_id, context=context, message=update.message)

        await send_video_file(update, context, video_path)
        return

    # TikTok: langsung unduh dan kirim
    if "tiktok.com" in url:
        await context.bot.send_message(chat_id=chat_id, text="🔄 TikTok video terdeteksi, sedang mengunduh...")
        video_path = download_tiktok(url)

        await send_video_file(update, context, video_path)
        return
    
    # Instagram: langsung unduh dan kirim
    if "instagram.com" in url:
        await context.bot.send_message(chat_id=chat_id, text="🔄 Instagram terdeteksi, sedang mengunduh...")
        video_path = download_instagram(url)
        await send_video_file(update, context, video_path)

    # Jika bukan sesi pemilihan kualitas, proses URL baru
    if "youtube.com" in url or "youtu.be" in url:
        if is_shorts(url):
            # Shorts langsung download tanpa pilih kualitas
            await context.bot.send_message(chat_id=chat_id, text="🔄 YouTube Shorts terdeteksi, langsung mengunduh video...")
            video_path = download_youtube(url, context=context, message=update.message)
            await send_video_file(update, context, video_path)
        else:
            # Video biasa, ambil kualitas dan minta user pilih
            qualities = get_available_qualities(url)
            if not qualities:
                await update.message.reply_text("❌ Tidak dapat mengambil kualitas video.")
                return

            user_sessions[chat_id] = {
                "await_quality": True,
                "qualities": qualities,
                "url": url,
            }

            msg = "Silahkan pilih kualitas video dengan mengirim nomor atau resolusi:\n"
            for i, (label, _) in enumerate(qualities, start=1):
                msg += f"{i}. {label}\n"
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Silahkan kirimkan URL video yang akan didownload")

async def send_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: str):
    chat_id = update.effective_chat.id

    if not video_path:
        await context.bot.send_message(chat_id=chat_id, text="❌ Gagal mengunduh video.")
        return

    await context.bot.send_message(chat_id=chat_id, text="Mengirim video, harap tunggu hingga 5 menit...")

    video_sent = False
    try:
        if os.path.getsize(video_path) <= 49 * 1024 * 1024:
            with open(video_path, "rb") as f:
                await context.bot.send_video(chat_id=chat_id, video=f)
        else:
            with open(video_path, "rb") as f:
                await context.bot.send_document(chat_id=chat_id, document=f)
        video_sent = True
    except Exception as e:
        print("Telegram send error:", e)
        await asyncio.sleep(5)
        if not video_sent:
            await context.bot.send_message(chat_id=chat_id, text="❌ Gagal mengirim video.")
    finally:
        os.remove(video_path)

def main():
    request = HTTPXRequest(
        connect_timeout=10.0,
        read_timeout=300.0,
        write_timeout=300.0,
        pool_timeout=60.0,
    )
    
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
