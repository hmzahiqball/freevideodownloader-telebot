import os
import uuid
import yt_dlp

def download_tiktok(url: str) -> str:
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join("downloads", filename)

    ydl_opts = {
        'outtmpl': filepath,
        'format': 'mp4',
        'quiet': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filepath
    except Exception as e:
        print("Download TikTok error:", e)
        return None
