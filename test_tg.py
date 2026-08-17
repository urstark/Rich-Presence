import os, requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

resp = requests.post(f"{BASE_URL}/sendRichMessage", json={
    "chat_id": CHANNEL_ID,
    "rich_message": {"markdown": "Hello"}
})
print("sendRichMessage:", resp.status_code, resp.text)

resp = requests.post(f"{BASE_URL}/sendMessage", json={
    "chat_id": CHANNEL_ID,
    "text": "Hello text"
})
print("sendMessage:", resp.status_code, resp.text)
