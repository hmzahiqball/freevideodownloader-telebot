import os
import uuid
import yt_dlp

def download_tiktok(url: str) -> str:
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join("downloads", filename)

    ydl_opts = {
        'outtmpl': filepath,
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filepath
    except Exception as e:
        print("Download TikTok error:", e)
        return None
