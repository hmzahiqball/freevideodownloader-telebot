import os
from pathlib import Path
from telegram.constants import ChatAction
import asyncio
from telegram.error import RetryAfter

async def send_video_file(update, context, video_path: str, url: str = None, video_cache=None, t=None):
    chat_id = update.effective_chat.id
    capt = "Downloaded By @FreeVideoDownloderBot"

    if not video_path or not os.path.exists(video_path):
        await update.message.reply_text(t("download_failed", chat_id=chat_id))
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

    file_ext = Path(video_path).suffix.lower()
    file_size = os.path.getsize(video_path)

    with open(video_path, "rb") as f:
        try:
            if file_ext in [".jpg", ".jpeg", ".png"]:
                msg = await context.bot.send_photo(chat_id=chat_id, photo=f, caption=capt)
                media_type = "photo"
            elif file_size <= 20 * 1024 * 1024:
                msg = await context.bot.send_video(chat_id=chat_id, video=f, caption=capt)
                media_type = "video"
            else:
                msg = await context.bot.send_document(chat_id=chat_id, document=f, caption=capt)
                media_type = "document"
        except (asyncio.TimeoutError, RetryAfter) as e:
            # Jangan kirim pesan ke user jika timeout/retry after
            print(f"Timeout or flood limit hit while sending media: {e}")
            return
        except Exception as e:
            print("Telegram send error:", e)
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
        print("File disimpan di cache")  # Added print statement

    print(f"Video Sent {video_path}")

    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            # Bersihkan folder induk jika kosong
            dir_path = os.path.dirname(video_path)
            if (dir_path != "downloads" and  # Jangan hapus folder downloads utama
                os.path.exists(dir_path) and 
                not os.listdir(dir_path)):
                os.rmdir(dir_path)
    except Exception as e:
        print("Failed to remove file:", e)
