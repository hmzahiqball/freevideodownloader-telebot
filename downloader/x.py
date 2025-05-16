import yt_dlp
import os

def download_x(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    # Tentukan tipe media berdasar ekstensi file
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        media_type = "photo"
    elif ext in ['.mp4', '.mkv', '.webm', '.mov']:
        media_type = "video"
    else:
        media_type = "document"  # fallback

    return media_type, filename
