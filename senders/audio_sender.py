# senders/audio_sender.py
async def send_audio_file(update, context, path, url, caption, video_cache):
    chat_id = update.effective_chat.id
    with open(path, 'rb') as f:
        msg = await context.bot.send_audio(chat_id=chat_id, audio=f, caption=caption)
        video_cache[url] = ("audio", msg.audio.file_id)
