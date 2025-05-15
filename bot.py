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
from downloader.youtube import download_youtube
from config import BOT_TOKEN
import asyncio

os.makedirs("downloads", exist_ok=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Silahkan kirimkan URL video yang akan didownload")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    if "youtube.com" in url or "youtu.be" in url:
        # Beri tahu user bahwa bot sedang mengetik / download
        await context.bot.send_message(chat_id=chat_id, text="Sedang mendownload video...")
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

        # Unduh video
        video_path = download_youtube(url, context=context, message=update.message)

        if video_path:
            await context.bot.send_message(chat_id=chat_id, text="Mengirim video, harap tunggu hingga 5 menit...")
            
            video_sent = False
            try:
                if os.path.getsize(video_path) <= 49 * 1024 * 1024:
                    await context.bot.send_video(chat_id=chat_id, video=open(video_path, "rb"))
                else:
                    await context.bot.send_document(chat_id=chat_id, document=open(video_path, "rb"))
                video_sent = True
            except Exception as e:
                print("Telegram send error:", e)
                # Tunggu beberapa detik, mungkin video tetap terkirim
                await asyncio.sleep(5)

                if not video_sent:
                    # Coba deteksi apakah video sudah muncul (opsional), atau beri pesan gagal
                    await context.bot.send_message(chat_id=chat_id, text="❌ Gagal mengirim video.")

            finally:
                os.remove(video_path)
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Gagal mengunduh video.")
    else:
        await update.message.reply_text("Silahkan kirimkan URL video yang akan didownload")

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
