# telegram_alert.py
import os, requests, time
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_accident_alert(filename, s3_url, action="Accident Detected"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    text = f"""
🚨 *SafeRide AI Alert* 🚨

🖼️ File: {filename}
🔗 URL: {s3_url}
⚡ Action: {action}
⏰ Time: {timestamp}
"""
    msg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(msg_url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

    if s3_url.lower().endswith((".jpg", ".jpeg", ".png")):
        photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        requests.post(photo_url, data={"chat_id": CHAT_ID, "photo": s3_url, "caption": f"🚦 SafeRide AI: {action}"})

    print("✅ Telegram alert sent!")
