# downloader/instagram.py
import yt_dlp
import os
import uuid

def download_instagram(url: str) -> list:
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)

    outtmpl = os.path.join(temp_dir, f"{uuid.uuid4()}_%(title)s.%(ext)s")
    ydl_opts = {
        'outtmpl': outtmpl,
        'format': 'bestaudio*+bestvideo*',
        'quiet': True,
        'noplaylist': False,  # Untuk mendukung carousel
        'cookiefile': 'cookies.txt',
        'skip_download': False,
    }

    file_paths = []

    def _hook(d):
        if d['status'] == 'finished':
            file_paths.append(d['filename'])

    ydl_opts['progress_hooks'] = [_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return file_paths
    except Exception as e:
        print("Instagram download error:", e)
        return []
