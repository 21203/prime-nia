import requests
import os
from dotenv import load_dotenv
from secure_auth import play_spotify_on_phone
from smart_home import control_tplink
from documents import open_doc, list_docs
import asyncio

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=5)
    except:
        pass

def handle_telegram_command(text: str):
    if not text:
        return
    text = text.lower().strip()

    if "play" in text and "on phone" in text:
        track = text.replace("play", "").replace("on phone", "").strip()
        msg = play_spotify_on_phone(track or None)
        send_telegram_message(msg)

    elif "turn on" in text and ("light" in text or "lamp" in text):
        asyncio.run(control_tplink("Bedroom Lamp", "on"))
        send_telegram_message("💡 Light turned ON.")

    elif "turn off" in text and ("light" in text or "lamp" in text):
        asyncio.run(control_tplink("Bedroom Lamp", "off"))
        send_telegram_message("💡 Light turned OFF.")

    elif "list documents" in text:
        docs = list_docs()
        send_telegram_message(f"📄 Documents: {', '.join(docs[:5])}" if docs else "No documents.")

    elif text.startswith("open ") and any(ext in text for ext in [".pdf", ".doc", ".txt"]):
        name = text[5:].strip()
        if open_doc(name):
            send_telegram_message(f"✅ Opening '{name}'")
        else:
            send_telegram_message("❌ File not found.")

    else:
        send_telegram_message("❓ Try: 'play jazz on phone', 'turn on lamp', or 'list documents'")