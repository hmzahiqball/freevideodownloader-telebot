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

def is_shorts(url: str) -> bool:
    # Deteksi URL Youtube Shorts
    return "youtube.com/shorts/" in url

def get_available_qualities(url: str):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            qualities = []
            # Ambil format video+audio mp4 progressive
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
                    res = f.get('format_note') or f.get('resolution') or f.get('format_id')
                    if res and res not in [q[0] for q in qualities]:
                        qualities.append((res, f['format_id']))
            return qualities
    except Exception as e:
        print("Error getting qualities:", e)
        return []

def download_youtube(url: str, format_id=None, context=None, message=None) -> str:
    global progress_message

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join("downloads", filename)

    ydl_opts = {
        'outtmpl': filepath,
        'quiet': True,
        'noplaylist': True,
        'progress_hooks': [hook],
    }
    if format_id:
        ydl_opts['format'] = format_id
    else:
        ydl_opts['format'] = 'best[ext=mp4]'

    if context and message:
        progress_message = context.bot.send_message(chat_id=message.chat_id, text="Mulai mengunduh...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filepath
    except Exception as e:
        print("Download error:", e)
        return None
