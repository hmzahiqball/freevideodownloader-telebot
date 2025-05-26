import asyncio
from telegram.constants import ChatAction
from downloader.youtube import download_youtube, get_available_qualities, is_shorts
from senders.video_sender import send_video_file
from state import t, video_cache, user_sessions

async def handle_youtube(update, context, url, capt):
    # Check single video cache first
    chat_id = update.effective_chat.id
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