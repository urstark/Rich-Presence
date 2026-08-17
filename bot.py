import os
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
MESSAGE_ID = os.getenv("TELEGRAM_MESSAGE_ID")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def build_message_text(state_manager):
    s = state_manager.state
    
    # Header
    manual = s["manual_status"]
    activity = s["current_activity"]
    start = s["activity_start_time"]
    about = s["custom_about"]
    
    status_emoji = {
        "Online": "🟢",
        "AFK": "🟡",
        "DND": "🔴",
        "Sleeping": "😴"
    }.get(manual, "🟢")
    
    lines = []
    lines.append(f"<b>{status_emoji} Live Status: {manual}</b>")
    if about:
        lines.append(f"<i>{about}</i>")
        
    lines.append("")
    if manual == "Sleeping" or not activity:
        lines.append("💤 <i>No active tasks right now...</i>")
    else:
        elapsed = state_manager.get_elapsed_str(start)
        lines.append(f"🔹 <b>{activity}</b>")
        lines.append(f"⏱ <i>{elapsed}</i>")
        
    lines.append("")
    lines.append("<b>[►] Last 7 Days Activity Summary</b>")
    lines.append("<pre>")
    lines.append("Date       | Activity")
    lines.append("-----------|-------------------")
    
    # Add history
    if not s["history"]:
        lines.append("No recent history...")
    else:
        added = 0
        for item in s["history"]:
            # Format time
            import datetime
            dt = datetime.datetime.fromtimestamp(item["timestamp"])
            day_str = dt.strftime("%m-%d")
            
            # format duration
            m = int(item["duration"] // 60)
            dur = f"{m}m" if m < 60 else f"{m//60}h {m%60}m"
            
            act_str = item["activity"][:15] + ("." if len(item["activity"]) > 15 else "")
            
            lines.append(f"{day_str:<10} | {act_str} ({dur})")
            added += 1
            if added >= 10: # Only show last 10 in the message to keep it clean
                break
    lines.append("</pre>")
    
    return "\n".join(lines)

def update_telegram_message(state_manager):
    if not TOKEN or not CHANNEL_ID:
        return
        
    text = build_message_text(state_manager)
    
    global MESSAGE_ID
    
    if not MESSAGE_ID or MESSAGE_ID == "0" or MESSAGE_ID == "":
        # Send new message
        resp = requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": CHANNEL_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_notification": True
        })
        if resp.status_code == 200:
            msg_id = resp.json()["result"]["message_id"]
            MESSAGE_ID = str(msg_id)
            # Update .env (naive replace)
            try:
                with open(".env", "r") as f:
                    env_data = f.read()
                env_data = env_data.replace("TELEGRAM_MESSAGE_ID=0", f"TELEGRAM_MESSAGE_ID={msg_id}")
                with open(".env", "w") as f:
                    f.write(env_data)
            except:
                pass
            print(f"Created new message with ID {msg_id}")
        else:
            print(f"Telegram error: {resp.text}")
    else:
        # Edit existing message
        resp = requests.post(f"{BASE_URL}/editMessageText", json={
            "chat_id": CHANNEL_ID,
            "message_id": int(MESSAGE_ID),
            "text": text,
            "parse_mode": "HTML"
        })
        if resp.status_code != 200:
            err_text = resp.text
            print(f"Telegram edit error: {err_text}")
            if "message to edit not found" in err_text or "message is not modified" not in err_text and resp.status_code == 400:
                if "message to edit not found" in err_text:
                    print("Message was deleted. Auto-healing by sending a new message...")
                    MESSAGE_ID = "0"
                    update_telegram_message(state_manager)
