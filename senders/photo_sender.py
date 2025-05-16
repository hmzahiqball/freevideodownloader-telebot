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
        except Exception as e:
            print("Telegram send photo error:", e)
            await update.message.reply_text(t("send_failed", chat_id=chat_id))
            return

    if url and msg and msg.photo and video_cache is not None:
        file_id = ("photo", msg.photo[-1].file_id)
        video_cache[url] = file_id

    print(f"Photo Sent {photo_path}")

    try:
        os.remove(photo_path)
    except Exception as e:
        print("Failed to remove photo file:", e)
