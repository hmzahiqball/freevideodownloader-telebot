import os
import json
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from downloader.youtube import download_youtube
from senders.video_sender import send_video_file
# from handlers.handle_language import handle_language_selection, handle_language_command
from handlers.handle_x import handle_x
from handlers.handle_tiktok import handle_tiktok
from handlers.handle_instagram import handle_instagram
from handlers.handle_youtube import handle_youtube
from handlers.handle_spotify import handle_spotify
from handlers.handle_soundcloud import handle_soundcloud
from state import t, video_cache, audio_cache, user_sessions, user_languages, LANGUAGE_CHOICE, handle_language_selection, handle_language_command
from config import BOT_TOKEN

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("ask_url", chat_id=update.effective_chat.id))

# --- Main Handler ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id
    capt = "Downloaded By @FreeVideoDownloderBot"

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
        await send_video_file(update, context, video_path, url_session, video_cache=video_cache, t=t)
        return

    # Handle X (Twitter)
    if "twitter.com" in url or "x.com" in url:
        await handle_x(update, context, url, capt)
        return

    # TikTok
    if "tiktok.com" in url:
        await handle_tiktok(update, context, url, capt)
        return

    # Instagram
    if "instagram.com" in url:
        await handle_instagram(update, context, url, capt)
        return
    
    # YouTube
    if "youtube.com" in url or "youtu.be" in url:
        await handle_youtube(update, context, url, capt)
        return
    
    # Spotify
    if "open.spotify.com" in url:
        await handle_spotify(update, context, url, capt)
        return
    
    # Soundcloud
    if "soundcloud.com" in url:
        await handle_soundcloud(update, context, url, capt)
        return

    # If URL is not recognized
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