import yt_dlp
import os
import uuid

progress_message = None  # Akan diisi oleh bot.py

def hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '')
        eta = d.get('eta', '')
        text = f"⬇️ Mengunduh... {percent} | {speed} | ETA: {eta}s"
        if progress_message:
            try:
                progress_message.edit_text(text)
            except:
                pass
    elif d['status'] == 'finished':
        if progress_message:
            try:
                progress_message.edit_text("✅ Unduhan selesai, mengirim video...")
            except:
                pass

def download_youtube(url: str, context=None, message=None) -> str:
    global progress_message

    # Nama file unik
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join("downloads", filename)

    ydl_opts = {
        'outtmpl': filepath,
        'format': 'best[ext=mp4]',
        'quiet': True,
        'noplaylist': True,
        'progress_hooks': [hook],
    }

    if context and message:
        progress_message = context.bot.send_message(chat_id=message.chat_id, text="Mulai mengunduh...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filepath
    except Exception as e:
        print("Download error:", e)
        return None
