# downloader/instagram.py
import yt_dlp
import os
import uuid

def download_instagram(url: str) -> str:
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join("downloads", filename)

    ydl_opts = {
        'outtmpl': filepath,
        'format': 'best[ext=mp4]',
        'quiet': True,
        'noplaylist': True,
        'cookiefile': 'cookies.txt',  # ← ini kuncinya
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filepath
    except Exception as e:
        print("Instagram download error:", e)
        return None
