import os
import uuid
import yt_dlp

def download_tiktok(url: str):
    """
    Mengunduh video TikTok dari URL.
    Mengembalikan tipe 'video' dan path file jika berhasil, selain itu (None, None).
    """

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join("downloads", filename)

    # Buat folder jika belum ada
    os.makedirs("downloads", exist_ok=True)

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
        return "video", filepath
    except Exception as e:
        print("Download TikTok error:", e)
        return None, None
