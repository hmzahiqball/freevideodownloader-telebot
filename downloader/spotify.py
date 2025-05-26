import os
import uuid
import subprocess

def download_spotify(url: str):
    """
    Download lagu dari Spotify menggunakan spotDL.
    Mengembalikan ('audio', path_file) jika sukses, selain itu (None, None).
    """
    filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join("downloads", filename)

    os.makedirs("downloads", exist_ok=True)

    command = [
        "spotdl",
        url,
        "--output", output_path,
        "--ffmpeg", "ffmpeg",  # Pastikan ffmpeg ke-detect
        "--overwrite", "force"
    ]

    try:
        subprocess.run(command, check=True)
        return "audio", output_path
    except Exception as e:
        print("Download Spotify error:", e)
        return None, None
