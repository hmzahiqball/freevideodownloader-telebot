from telegram import Update, InputMediaPhoto
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes,
)

video_cache = {}     # url -> (type, file_id) or special keys for media groups

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