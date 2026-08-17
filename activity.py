import requests
import urllib.parse
from datetime import datetime, timezone

LANYARD_API = "https://api.lanyard.rest/v1/users/{user_id}"
AW_API = "http://localhost:5600/api/0/buckets"

WHITELIST = {
    "vscodium": "Coding in VSCodium",
    "obsidian": "Taking notes in Obsidian",
    "antigravity": "Coding/Programming",
    "waydroid": "Waydroid Android Emulator",
    "discord": "Using Discord",
    "telegram": "Using Telegram",
    "telegramdesktop": "Using Telegram"
}

def fetch_lanyard(user_id: str):
    if not user_id:
        return None
    try:
        resp = requests.get(LANYARD_API.format(user_id=user_id), timeout=2)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            # Check for spotify
            if data.get("listening_to_spotify") and data.get("spotify"):
                spotify = data["spotify"]
                return f"🎵 Listening: {spotify['song']} by {spotify['artist']}"
            
            # Check for other activities
            activities = data.get("activities", [])
            for act in activities:
                if act["type"] == 0: # Playing
                    return f"🎮 Playing: {act['name']}"
    except Exception as e:
        print(f"Lanyard error: {e}")
    return None

def fetch_aw():
    try:
        resp = requests.get(AW_API, timeout=2)
        if resp.status_code != 200:
            return None, False
        buckets = resp.json()
        
        window_bucket = next((k for k in buckets.keys() if "aw-watcher-window" in k), None)
        web_bucket = next((k for k in buckets.keys() if "aw-watcher-web" in k), None)
        afk_bucket = next((k for k in buckets.keys() if "aw-watcher-afk" in k), None)

        is_afk = False
        if afk_bucket:
            # Check if currently AFK (this requires getting the latest event, which might be tricky if aw doesn't return 'status' easily via buckets endpoint,
            # we need to query the events. Let's query events for AFK)
            events_resp = requests.get(f"{AW_API}/{afk_bucket}/events?limit=1", timeout=1)
            if events_resp.status_code == 200:
                events = events_resp.json()
                if events and events[0]["data"].get("status") == "afk":
                    is_afk = True

        activity_str = None
        
        # 1. Check Window
        if window_bucket:
            events_resp = requests.get(f"{AW_API}/{window_bucket}/events?limit=1", timeout=1)
            if events_resp.status_code == 200:
                events = events_resp.json()
                if events:
                    app_name = events[0]["data"].get("app", "").lower()
                    title = events[0]["data"].get("title", "")
                    
                    # Chrome/Browser parsing
                    if "chrome" in app_name or "brave" in app_name or "firefox" in app_name:
                        # Let's query web bucket for better URL info
                        activity_str = parse_chrome_tab(web_bucket)
                    else:
                        # Check whitelist
                        for key, value in WHITELIST.items():
                            if key in app_name:
                                activity_str = value
                                break
                            
        return activity_str, is_afk
    except Exception as e:
        print(f"AW error: {e}")
        return None, False

def parse_chrome_tab(web_bucket):
    if not web_bucket:
        return "🌐 Using Chrome"
    try:
        events_resp = requests.get(f"{AW_API}/{web_bucket}/events?limit=1", timeout=1)
        if events_resp.status_code == 200:
            events = events_resp.json()
            if events:
                url = events[0]["data"].get("url", "")
                title = events[0]["data"].get("title", "")
                
                if "youtube.com" in url:
                    # Title is usually "Video Name - YouTube"
                    vid_title = title.replace(" - YouTube", "")
                    return f"🎵 Watching/Listening: {vid_title}"
                elif "github.com" in url:
                    if title == "GitHub":
                        return "👨‍💻 Exploring GitHub"
                    elif "Private" in title: # naive check
                        return "👨‍💻 Working on a private repo"
                    else:
                        # Remove " - GitHub"
                        repo_name = title.split(" - ")[0].split("·")[0].strip()
                        return f"👨‍💻 Working on GitHub: {repo_name}"
                else:
                    return "🌐 Using Chrome"
    except:
        pass
    return "🌐 Using Chrome"

def get_current_status(lanyard_user_id: str):
    """Returns (Activity String, is_afk)"""
    # 1. Try Discord/Lanyard first
    lanyard_act = fetch_lanyard(lanyard_user_id)
    if lanyard_act:
        # Also need to check if PC is AFK to sleep
        _, is_afk = fetch_aw()
        return lanyard_act, is_afk
    
    # 2. Try ActivityWatch local
    aw_act, is_afk = fetch_aw()
    if aw_act:
        return aw_act, is_afk
        
    return None, is_afk
