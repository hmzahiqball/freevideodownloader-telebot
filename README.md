# 🎬 FreeVideoDownloderBot - Telegram Bot for Media Downloads

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blueviolet)
![License](https://img.shields.io/github/license/yourusername/FreeVideoDownloderBot)
![Platform](https://img.shields.io/badge/Platform-Telegram-informational)

> A powerful and private Telegram bot to download videos and photos from popular platforms like TikTok, Instagram, X (Twitter), and YouTube — right from your chat. 🚀

---

## 🤖 About the Bot

**FreeVideoDownloderBot** is a feature-rich Telegram bot built in Python, designed to make video and photo downloads effortless. It supports a wide range of platforms and formats with high-quality options, designed for speed and privacy.

**Telegram Bot Username: [`@FreeVideoDownloderBot`](https://t.me/FreeVideoDownloderBot)**

---

## 📦 Features

✅ **X (formerly Twitter)**  
• Download both **videos** and **photos** from public X posts.

✅ **Instagram**  
• Download **videos** and **photos** from Instagram posts and reels.

✅ **TikTok**  
• Download **videos** from regular TikTok posts (non-slideshow).  
• *(TikTok slideshows support is in development.)*

✅ **YouTube Shorts**  
• Download **YouTube Shorts** videos instantly.

✅ **YouTube (Full Videos)**  
• Choose from **multiple quality options** (360p, 720p, 1080p, etc).  
• Download high-quality YouTube videos without watermarks.

---

## 🛠 Tech Stack

- [Python 3.10+](https://www.python.org/)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Selenium (for TikTok slideshows)](https://www.selenium.dev/)
- AsyncIO + multithreading for performance

---

## 🚀 Getting Started

Clone the repo:

```bash
git clone https://github.com/hmzahiqball/freevideodownloader-telebot.git
cd freevideodownloader-telebot
```

Install requirements:
```bash
pip install -r requirements.txt
```

Set your environment variables (e.g. BOT_TOKEN) or edit config.py.

Start the bot:
```bash
python bot.py
```

## 🧠 How It Works
The bot automatically detects the source of the URL and processes it accordingly. Downloaded media is either:

- Sent as video/photo messages
- Or sent in albums (for Instagram & X photos)

YouTube downloads offer selectable resolution for longer videos.

## 🔒 Privacy & Fair Use
This bot is intended for educational and personal use only. Please respect copyright and terms of service of each platform.
No data is logged or stored — all downloads are temporary and auto-deleted.

## 💡 Future Improvements
- ✅ TikTok slideshow support (in progress)
- ⏳ SoundCloud support
- ⏳ Media Sender optimization
- ⏳ Media size optimization

## 🙌 Contribution
Pull requests are welcome! If you find a bug or want to add a feature, feel free to open an issue or fork the project.

## 📄 License
This project is licensed under the MIT License. See the LICENSE file for details.

## 👤 Author
Developed with ❤️ by hmzahiqball
🔗 Telegram Bot: @FreeVideoDownloderBot
