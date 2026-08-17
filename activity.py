import requests
import urllib.parse
from datetime import datetime, timezone

from config import load_config

LANYARD_API = "https://api.lanyard.rest/v1/users/{user_id}"
AW_API = "http://localhost:5600/api/0/buckets"

def fetch_lanyard(user_id: str):
    if not user_id:
        return []
    acts = []
    try:
        resp = requests.get(LANYARD_API.format(user_id=user_id), timeout=2)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            # Check for spotify
            if data.get("listening_to_spotify") and data.get("spotify"):
                spotify = data["spotify"]
                acts.append(f"🎵 Listening: {spotify['song']} by {spotify['artist']}")
            
            # Check for other activities
            activities = data.get("activities", [])
            for act in activities:
                if act["type"] == 0: # Playing
                    acts.append(f"🎮 Playing: {act['name']}")
    except Exception as e:
        print(f"Lanyard error: {e}")
    return acts

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
                    
                    # Browser parsing
                    config = load_config()
                    is_browser = any(b in app_name for b in config.get("browsers", ["chrome", "brave", "firefox", "edge", "opera"]))
                    
                    if is_browser:
                        # Let's query web bucket for better URL info
                        activity_str = parse_chrome_tab(web_bucket)
                    else:
                        # Check whitelist
                        for key, value in config.get("apps", {}).items():
                            if key in app_name:
                                activity_str = value
                                break
                            
        return activity_str, is_afk
    except Exception as e:
        print(f"AW error: {e}")
        return None, False

def parse_chrome_tab(web_bucket):
    config = load_config()
    default_str = config.get("default_website", "Doomscrolling the web 📱")
    if not web_bucket:
        return default_str
    try:
        events_resp = requests.get(f"{AW_API}/{web_bucket}/events?limit=1", timeout=1)
        if events_resp.status_code == 200:
            events = events_resp.json()
            if events:
                url = events[0]["data"].get("url", "")
                title = events[0]["data"].get("title", "")
                
                # Cleanup common browser suffixes from title
                suffixes = [" - YouTube", " - Google Chrome", " - Mozilla Firefox", " - Brave", " - Vivaldi", " - Opera", " - GitHub"]
                clean_title = title
                for s in suffixes:
                    if clean_title.endswith(s):
                        clean_title = clean_title[:-len(s)]
                clean_title = clean_title.strip()

                for domain, act_str in config.get("websites", {}).items():
                    if domain in url:
                        # format with dynamic title
                        if "{title}" in act_str:
                            return act_str.replace("{title}", clean_title)
                        return act_str
                        
                return default_str
    except:
        pass
    return default_str

def get_current_status(lanyard_user_id: str):
    """Returns (Activity String, is_afk)"""
    acts = []
    
    # 1. Try Discord/Lanyard first
    lanyard_acts = fetch_lanyard(lanyard_user_id)
    acts.extend(lanyard_acts)
    
    # 2. Try ActivityWatch local
    aw_act, is_afk = fetch_aw()
    if aw_act:
        acts.append(aw_act)
    
    if acts:
        return " | ".join(acts), is_afk
        
    return None, is_afk
