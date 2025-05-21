import os
from telegram.constants import ChatAction

async def send_photo_file(update, context, photo_path: str, url: str = None, video_cache=None, t=None):
    chat_id = update.effective_chat.id
    capt = "Downloaded By @FreeVideoDownloderBot"

    if not photo_path or not os.path.exists(photo_path):
        await update.message.reply_text(t("download_failed", chat_id=chat_id))
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    with open(photo_path, "rb") as f:
        try:
            msg = await context.bot.send_photo(chat_id=chat_id, photo=f, caption=capt)
            
            # Simpan ke cache jika ada URL
            if url and msg and video_cache is not None:
                if msg.photo:
                    file_id = ("photo", msg.photo[-1].file_id)  # Gunakan ukuran terbesar
                    video_cache[url] = file_id
                    print("Media saved to cache")
                else:
                    print("Failed to save media to cache")
        except Exception as e:
            print("Telegram send photo error:", e)
            await update.message.reply_text(t("send_failed", chat_id=chat_id))
            return

    if url and msg and video_cache is not None:
        if msg.video:
            file_id = ("video", msg.video.file_id)
        elif msg.document:
            file_id = ("document", msg.document.file_id)
        elif msg.photo:
            file_id = ("photo", msg.photo[-1].file_id)  # Use largest photo size
        else:
            return
            
        video_cache[url] = file_id
        print("Media saved to cache")

    print(f"Photo Sent {photo_path}")
    
def cleanup_empty_dirs(path, stop_at="downloads"):
    while True:
        if not os.path.isdir(path) or os.listdir(path):
            break  # Folder tidak kosong atau bukan direktori
        try:
            os.rmdir(path)
        except Exception as e:
            break
        path = os.path.dirname(path)
        if os.path.basename(path) == stop_at:
            break
