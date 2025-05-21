### --- downloader/x.py ---
import yt_dlp
import os
import subprocess
import glob

def download_x(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best',
    }

    downloaded_files = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            downloaded_files.append(filename)
    except Exception:
        subprocess.run([
            'gallery-dl', '-d', 'downloads', url
        ], check=True)

        files = sorted(glob.glob('downloads/**/*.*', recursive=True), key=os.path.getmtime, reverse=True)
        if not files:
            raise Exception("❌ Tidak ada file yang terunduh.")
        downloaded_files.extend(files[:10])  # Ambil 10 file terbaru (jika ada banyak)

    # Kategorikan file
    results = []
    for filename in downloaded_files:
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            media_type = "photo"
        elif ext in ['.mp4', '.mkv', '.webm', '.mov']:
            media_type = "video"
        else:
            media_type = "document"
        results.append((media_type, filename))

    return results
