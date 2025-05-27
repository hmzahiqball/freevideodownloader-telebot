import os
import asyncio
from telegram import InputMediaPhoto
from telegram.constants import ChatAction
from downloader.instagram import download_instagram, convert_webp_to_jpg
from senders.video_sender import send_video_file
from senders.photo_sender import send_photo_file, cleanup_empty_dirs
from senders.media_group_sender import send_media_group_from_cache
from state import t, video_cache

async def handle_instagram(update, context, url, capt):
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
                    print(f"Convert failed {path}: {e}")
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