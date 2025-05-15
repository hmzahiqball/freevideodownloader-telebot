import httpx
import os
import uuid
import requests
from bs4 import BeautifulSoup
import yt_dlp
import asyncio

def download_tiktok(url: str):
    if "/photo/" in url:
        # Handle slideshow/foto
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
            }
            r = requests.get(url, headers=headers)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")

            # Cari semua tag img yang mungkin berisi foto slideshow
            # Berdasarkan inspeksi TikTok, biasanya ada <img> dengan src foto slideshow
            imgs = soup.find_all("img")

            img_urls = []
            for img in imgs:
                src = img.get("src")
                if src and "p16-tiktok-sign" in src:
                    img_urls.append(src)

            if not img_urls:
                print("Tidak ditemukan foto slideshow.")
                return None, None

            saved_paths = []
            for img_url in img_urls:
                response = requests.get(img_url, headers=headers)
                response.raise_for_status()

                filename = f"{uuid.uuid4()}.jpg"
                filepath = os.path.join("downloads", filename)

                with open(filepath, "wb") as f:
                    f.write(response.content)
                saved_paths.append(filepath)

            return "images", saved_paths
        except Exception as e:
            print("Error download TikTok slideshow:", e)
            return None, None

    else:
        # Handle video biasa pakai yt_dlp
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
            return "video", filepath
        except Exception as e:
            print("Download TikTok error:", e)
            return None, None
        
async def download_tiktok_photo_gallery(url: str) -> list[str]:
    images = []
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            # Cari tag gambar khusus (contoh):
            for img_tag in soup.select("img"):  
                img_url = img_tag.get("src")
                if img_url and "twimg.com" in img_url:  # filter url gambar tiktok
                    file_name = os.path.join("downloads", os.path.basename(img_url.split("?")[0]))
                    img_data = await client.get(img_url)
                    with open(file_name, "wb") as f:
                        f.write(img_data.content)
                    images.append(file_name)
        return images
    except Exception as e:
        print("Error download_tiktok_photo_gallery:", e)
        return []
