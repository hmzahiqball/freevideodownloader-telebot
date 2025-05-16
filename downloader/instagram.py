import yt_dlp
import os
import uuid
import subprocess
import glob
import shutil

def download_instagram(url: str) -> list:
    session_dir = os.path.join("downloads", str(uuid.uuid4()))
    os.makedirs(session_dir, exist_ok=True)

    # 1. Coba pakai yt-dlp (untuk video)
    outtmpl = os.path.join(session_dir, "%(title)s.%(ext)s")
    ydl_opts = {
        'outtmpl': outtmpl,
        'format': 'bestaudio*+bestvideo*',
        'quiet': True,
        'noplaylist': False,
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
        if file_paths:
            return file_paths
    except Exception as e:
        print("yt_dlp Instagram error:", e)

    # 2. Fallback ke gallery-dl (untuk image)
    try:
        subprocess.run(
            ["gallery-dl", "-d", session_dir, "--cookies", "cookies.txt", url],
            check=True
        )
        # Ambil semua file media di session_dir
        return [f for f in glob.glob(os.path.join(session_dir, "**", "*"), recursive=True) if os.path.isfile(f)]
    except Exception as e:
        print("gallery-dl Instagram error:", e)
        return []
