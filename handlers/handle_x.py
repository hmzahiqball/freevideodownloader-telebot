import os
import asyncio
from telegram import InputMediaPhoto
from telegram.constants import ChatAction
from downloader.x import download_x
from senders.video_sender import send_video_file
from senders.photo_sender import send_photo_file
from senders.media_group_sender import send_media_group_from_cache
from state import t, video_cache

async def handle_x(update, context, url, capt):
    # Check if media group cache exists for this URL
    chat_id = update.effective_chat.id
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