import os
from pathlib import Path
from telegram.constants import ChatAction

async def send_video_file(update, context, video_path: str, url: str = None, video_cache=None, t=None):
    chat_id = update.effective_chat.id
    capt = "Downloaded By @FreeVideoDownloderBot"

    if not video_path or not os.path.exists(video_path):
        await update.message.reply_text(t("download_failed", chat_id=chat_id))
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

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
        except Exception as e:
            print("Telegram send error:", e)
            await update.message.reply_text(t("send_failed", chat_id=chat_id))
            return

    if url and msg and (msg.photo or msg.video or msg.document) and video_cache is not None:
        file_id = (media_type, (msg.video or msg.document or msg.photo[-1]).file_id)
        video_cache[url] = file_id

    print(f"Video Sent {video_path}")

    try:
        os.remove(video_path)
    except Exception as e:
        print("Failed to remove file:", e)
