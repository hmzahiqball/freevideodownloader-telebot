import yt_dlp
import os
import subprocess
import glob
import hashlib
from PIL import Image

def get_url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

def convert_webp_to_jpg(webp_path):
    jpg_path = webp_path.replace(".webp", ".jpg")
    im = Image.open(webp_path).convert("RGB")
    im.save(jpg_path, "JPEG")
    os.remove(webp_path)  # Hapus file .webp jika tidak dibutuhkan
    return jpg_path

def download_instagram(url: str) -> list:
    session_dir = os.path.join("downloads", get_url_hash(url))
    os.makedirs(session_dir, exist_ok=True)

    # 1. Coba pakai yt-dlp (untuk video)
    output_template = os.path.join(session_dir, "%(title)s.%(ext)s")  # untuk yt-dlp
    output_dir = session_dir  # untuk gallery-dl
    ydl_opts = {
        'outtmpl': output_template,
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
            ["gallery-dl", "-d", output_dir, "--cookies", "cookies.txt", url],
            check=True
        )
        # Ambil semua file media di session_dir
        return [f for f in glob.glob(os.path.join(output_dir, "**", "*"), recursive=True) if os.path.isfile(f)]
    except Exception as e:
        print("gallery-dl Instagram error:", e)
        return []
