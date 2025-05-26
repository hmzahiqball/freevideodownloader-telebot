import asyncio
from telegram.constants import ChatAction
from downloader.tiktok import download_tiktok
from senders.video_sender import send_video_file
from state import t, video_cache

async def handle_tiktok(update, context, url, capt):
    # Check cache
    chat_id = update.effective_chat.id
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