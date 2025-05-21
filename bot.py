import os
import asyncio
import json
from pathlib import Path
from telegram import Update, InputMediaPhoto, InputMediaVideo
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
from downloader.instagram import download_instagram, convert_webp_to_jpg
from downloader.x import download_x
from senders.video_sender import send_video_file
from senders.photo_sender import send_photo_file, cleanup_empty_dirs
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
video_cache = {}     # url -> (type, file_id) or special keys for media groups


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


# --- Helper Functions ---
async def send_media_group_from_cache(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, media_type: str):
    """Send media group from cache"""
    chat_id = update.effective_chat.id
    capt = "Downloaded By @FreeVideoDownloderBot"
    
    # Get media group items from cache
    cache_key = f"{url}_{media_type}_mediagroup"
    if cache_key not in video_cache:
        return False
    
    media_group_data = video_cache[cache_key]
    
    # Prepare media group
    media_group = []
    for i, (item_type, file_id) in enumerate(media_group_data):
        if item_type == "photo":
            if i == 0:
                media_group.append(InputMediaPhoto(file_id, caption=capt))
            else:
                media_group.append(InputMediaPhoto(file_id))
    
    if media_group:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
        await update.message.reply_media_group(media=media_group)
        return True
    
    return False


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
        # Check if media group cache exists for this URL
        photos_sent = await send_media_group_from_cache(update, context, url, "photo")
        
        # Check if video cache exists for this URL
        video_cache_key = f"{url}_video"
        if video_cache_key in video_cache:
            media_type, file_id = video_cache[video_cache_key]
            if photos_sent:
                await asyncio.sleep(1)  # Small delay between media group and video
            
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
            await context.bot.send_video(chat_id=chat_id, video=file_id, caption=capt)
            print("X media sent from cache.")
            return
            
        # If we've sent photos but no video was cached or vice versa, continue downloading
        if photos_sent:
            print("X photos sent from cache, no video cached")
            return
        
        await update.message.reply_text(t("x_media_detected", chat_id=chat_id))
        try:
            results = await asyncio.to_thread(download_x, url)
        except Exception as e:
            print("Download X error:", e)
            await update.message.reply_text(t("x_download_error", chat_id=chat_id))
            return

        # Separate photos and videos
        photos = [r for r in results if r[0] == "photo"]
        videos = [r for r in results if r[0] == "video"]
        documents = [r for r in results if r[0] == "document"]
        
        # Send photos as media group if multiple
        if len(photos) > 0:
            if len(photos) > 1:
                media_group = []
                temp_files = []
                for i, (_, path) in enumerate(photos):
                    f = open(path, 'rb')
                    temp_files.append((f, path))
                    if i == 0:
                        media_group.append(InputMediaPhoto(f, caption=capt))
                    else:
                        media_group.append(InputMediaPhoto(f))
                
                msgs = await update.message.reply_media_group(media=media_group)
                
                # Save to cache
                media_group_cache = []
                for i, msg in enumerate(msgs):
                    if msg.photo:
                        media_group_cache.append(("photo", msg.photo[-1].file_id))
                
                if media_group_cache:
                    video_cache[f"{url}_photo_mediagroup"] = media_group_cache
                
                # Cleanup temp files
                for f, path in temp_files:
                    f.close()
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception as e:
                            print(f"Error removing file {path}: {e}")
            else:
                # Single photo
                await send_photo_file(update, context, photos[0][1], url, video_cache=video_cache, t=t)
        
        # Send videos
        for _, video_path in videos:
            # Add a small delay between media group and video
            if photos:
                await asyncio.sleep(1)
            await send_video_file(update, context, video_path, f"{url}_video", video_cache=video_cache, t=t)
            
        # Send documents
        for _, doc_path in documents:
            await context.bot.send_document(chat_id=chat_id, document=open(doc_path, "rb"))
            try:
                os.remove(doc_path)
            except Exception as e:
                print(f"Error removing document {doc_path}: {e}")
        
        return

    # TikTok
    if "tiktok.com" in url:
        # Check cache
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

    # Instagram
    if "instagram.com" in url:
        # Check if media group cache exists for this URL
        photos_sent = await send_media_group_from_cache(update, context, url, "photo")
        
        # Check if video cache exists for this URL
        video_cache_key = f"{url}_video"
        if video_cache_key in video_cache:
            media_type, file_id = video_cache[video_cache_key]
            if photos_sent:
                await asyncio.sleep(1)  # Small delay between media group and video
            
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
            await context.bot.send_video(chat_id=chat_id, video=file_id, caption=capt)
            print("Instagram video sent from cache.")
            return
            
        # If we've sent photos but no video was cached or vice versa, continue downloading
        if photos_sent:
            print("Instagram photos sent from cache, no video cached")
            return
            
        await update.message.reply_text(t("instagram_detected", chat_id=chat_id))
        try:
            file_paths = await asyncio.to_thread(download_instagram, url)

            video_paths = [f for f in file_paths if f.lower().endswith(".mp4")]
            image_paths = [f for f in file_paths if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]

            # Convert .webp to .jpg and track which files we created
            converted_files = {}
            new_image_paths = []

            for path in image_paths:
                if path.lower().endswith(".webp"):
                    try:
                        new_path = convert_webp_to_jpg(path)
                        new_image_paths.append(new_path)
                        converted_files[path] = new_path  # Track original → converted
                    except Exception as e:
                        print(f"Gagal konversi {path}: {e}")
                        # Fallback to original if conversion fails
                        new_image_paths.append(path)
                else:
                    new_image_paths.append(path)

            image_paths = new_image_paths
            image_paths.sort(key=lambda x: os.path.getctime(x))

            # Send photos first
            if len(image_paths) > 0:
                if len(image_paths) == 1:
                    path = image_paths[0]
                    await send_photo_file(update, context, path, url=f"{url}_photo_0", video_cache=video_cache, t=t)
                    # Cleanup the file we sent
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception as e:
                        print(f"Cleanup error: {e}")
                elif len(image_paths) > 1:
                    media_group = []
                    temp_files = []
                    for i, path in enumerate(image_paths):
                        f = open(path, 'rb')
                        temp_files.append((f, path))
                        if i == 0:
                            media_group.append(InputMediaPhoto(f, caption=capt))
                        else:
                            media_group.append(InputMediaPhoto(f))
                    
                    msgs = await update.message.reply_media_group(media=media_group)
                    
                    # Save to cache for future use
                    media_group_cache = []
                    for i, msg in enumerate(msgs):
                        if msg.photo:
                            media_group_cache.append(("photo", msg.photo[-1].file_id))
                    
                    if media_group_cache:
                        video_cache[f"{url}_photo_mediagroup"] = media_group_cache
                    
                    # Cleanup temp files
                    for f, path in temp_files:
                        f.close()
                        if os.path.exists(path):
                            try:
                                os.remove(path)
                            except Exception as e:
                                print(f"Error removing file {path}: {e}")

            # Send videos after photos
            if video_paths:
                # Add a small delay between media group and video
                if image_paths:
                    await asyncio.sleep(1)
                    
                for path in video_paths:
                    await send_video_file(update, context, path, f"{url}_video", video_cache=video_cache, t=t)
                    
            # Clean up directories
            for path in image_paths + video_paths:
                if os.path.exists(os.path.dirname(path)):
                    cleanup_empty_dirs(os.path.dirname(path), stop_at="downloads")
                    
            return
        except Exception as e:
            print("Download Instagram error:", e)
            await update.message.reply_text(t("download_failed", chat_id=chat_id))
            return
    
    # YouTube
    if "youtube.com" in url or "youtu.be" in url:
        # Check single video cache first
        if url in video_cache:
            media_type, file_id = video_cache[url]
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
            await context.bot.send_video(chat_id=chat_id, video=file_id, caption=capt)
            print("YouTube video sent from cache.")
            return
            
        if is_shorts(url):
            await update.message.reply_text(t("youtube_shorts_detected", chat_id=chat_id))
            try:
                video_path = await asyncio.to_thread(download_youtube, url, context=context, message=update.message)
            except Exception as e:
                print("Download YouTube shorts error:", e)
                await update.message.reply_text(t("download_failed", chat_id=chat_id))
                return
            await send_video_file(update, context, video_path, url, video_cache=video_cache, t=t)
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