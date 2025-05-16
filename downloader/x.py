import yt_dlp
import os
import subprocess
import glob

def download_x(url):
    # Gunakan yt-dlp untuk mencoba download video
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception:
        # Jika gagal (kemungkinan karena itu foto atau galeri), gunakan gallery-dl
        subprocess.run([
            'gallery-dl', '-d', 'downloads', url
        ], check=True)

        # Ambil file terbaru dari folder downloads
        files = sorted(glob.glob('downloads/**/*.*', recursive=True), key=os.path.getmtime, reverse=True)
        if not files:
            raise Exception("❌ Tidak ada file yang terunduh.")

        filename = files[0]  # Ambil file terbaru

    # Tentukan tipe media berdasar ekstensi
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        media_type = "photo"
    elif ext in ['.mp4', '.mkv', '.webm', '.mov']:
        media_type = "video"
    else:
        media_type = "document"  # fallback

    return media_type, filename
