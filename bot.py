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
        "Online": "✨",
        "AFK": "☕",
        "DND": "🔕",
        "Sleeping": "💤"
    }.get(manual, "✨")
    
    lines = []
    lines.append(f"# {status_emoji} Status: {manual}")
    if about:
        lines.append(f"*{about}*")
    lines.append("")
        
    lines.append("| Current Activity | Elapsed |")
    lines.append("|---|---|")
    
    if manual == "Sleeping":
        lines.append("| 💤 *I am currently sleeping* | - |")
    elif not activity:
        lines.append("| 💤 *No active tasks...* | - |")
    else:
        elapsed = state_manager.get_elapsed_str(start)
        safe_activity = activity.replace("|", "/")
        lines.append(f"| 👻 {safe_activity} | ⏱ {elapsed} |")
        
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>👀 Last 7 Days Activity Summary</summary>")
    lines.append("")
    lines.append("| Date | Activity | Duration |")
    lines.append("|---|---|---|")
    
    # Add history
    if not s["history"]:
        lines.append("| | No recent history... | |")
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
            
            act_str = item["activity"][:20] + ("." if len(item["activity"]) > 20 else "")
            # escape pipes for markdown tables
            act_str = act_str.replace("|", "/")
            
            lines.append(f"| {day_str} | {act_str} | {dur} |")
            added += 1
            if added >= 10: # Only show last 10 in the message to keep it clean
                break
    
    lines.append("")
    lines.append("</details>")
    
    return "\n".join(lines)

def update_telegram_message(state_manager):
    if not TOKEN or not CHANNEL_ID:
        return
        
    text = build_message_text(state_manager)
    
    global MESSAGE_ID
    
    if not MESSAGE_ID or MESSAGE_ID == "0" or MESSAGE_ID == "":
        # Send new message
        resp = requests.post(f"{BASE_URL}/sendRichMessage", json={
            "chat_id": CHANNEL_ID,
            "rich_message": {"markdown": text},
            "disable_notification": True
        })
        if resp.status_code == 200:
            msg_id = resp.json()["result"]["message_id"]
            MESSAGE_ID = str(msg_id)
            # Update .env (naive replace)
            try:
                import re
                with open(".env", "r") as f:
                    env_data = f.read()
                env_data = re.sub(r"TELEGRAM_MESSAGE_ID=.*", f"TELEGRAM_MESSAGE_ID={msg_id}", env_data)
                with open(".env", "w") as f:
                    f.write(env_data)
            except:
                pass
            print(f"Created new rich message with ID {msg_id}")
        else:
            print(f"Telegram sendRichMessage error: {resp.text}")
    else:
        # Edit existing message
        resp = requests.post(f"{BASE_URL}/editMessageText", json={
            "chat_id": CHANNEL_ID,
            "message_id": int(MESSAGE_ID),
            "rich_message": {"markdown": text}
        })
        if resp.status_code != 200:
            err_text = resp.text
            if "message is not modified" in err_text:
                print("Message content unchanged. Telegram skipped the edit.")
            else:
                print(f"Telegram edit error: {err_text}")
                
            if "message to edit not found" in err_text:
                print("Message was deleted. Auto-healing by sending a new message...")
                MESSAGE_ID = "0"
                update_telegram_message(state_manager)
        else:
            print(f"Successfully edited rich message ID {MESSAGE_ID}")
