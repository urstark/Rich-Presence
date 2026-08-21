import requests
import urllib.parse
from datetime import datetime, timezone
import re
import subprocess

from config import load_config

LANYARD_API = "https://api.lanyard.rest/v1/users/{user_id}"
AW_API = "http://localhost:5600/api/0/buckets"

CURRENT_YT_URL = ""
CURRENT_YT_IS_SONG = False

def is_event_stale(event: dict, max_age: int = 120) -> bool:
    try:
        ts_str = event.get("timestamp", "")
        if not ts_str: return True
        
        ts_str = ts_str.replace("Z", "+00:00")
        if "." in ts_str:
            base, frac_tz = ts_str.split(".", 1)
            if "+" in frac_tz:
                frac, tz = frac_tz.split("+", 1)
                tz = "+" + tz
            elif "-" in frac_tz:
                frac, tz = frac_tz.split("-", 1)
                tz = "-" + tz
            else:
                frac = frac_tz
                tz = "+00:00"
            ts_str = f"{base}.{frac[:6]}{tz}"
            
        dt = datetime.fromisoformat(ts_str)
        end = dt.timestamp() + event.get("duration", 0)
        now = datetime.now(timezone.utc).timestamp()
        return (now - end) > max_age
    except:
        return False

def is_youtube_song(url: str, title: str) -> bool:
    global CURRENT_YT_URL, CURRENT_YT_IS_SONG
    
    if url == CURRENT_YT_URL:
        return CURRENT_YT_IS_SONG
        
    CURRENT_YT_URL = url
    
    if "music.youtube.com" in url:
        CURRENT_YT_IS_SONG = True
        return True
        
    # Fast heuristic first
    lower_title = title.lower()
    song_keywords = ["official music video", "official video", "official audio", "lyrics", "music video", "mashup", "lofi", "cover", "mix", "remix", "song", "album"]
    if any(x in lower_title for x in song_keywords):
        CURRENT_YT_IS_SONG = True
        return True
        
    # Smart scraping for Category (YouTube officially tags all licensed music with this category)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=2)
        if resp.status_code == 200:
            match = re.search(r'itemprop="genre" content="([^"]+)"', resp.text)
            if match and match.group(1) == "Music":
                CURRENT_YT_IS_SONG = True
                return True
    except:
        pass
        
    CURRENT_YT_IS_SONG = False
    return False

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

        acts = []
        
        # 1. Check Window
        if window_bucket:
            events_resp = requests.get(f"{AW_API}/{window_bucket}/events?limit=1", timeout=1)
            if events_resp.status_code == 200:
                events = events_resp.json()
                if events and not is_event_stale(events[0], max_age=180):
                    app_name = events[0]["data"].get("app", "").lower()
                    title = events[0]["data"].get("title", "")
                    
                    # Browser parsing
                    config = load_config()
                    is_browser = any(b in app_name for b in config.get("browsers", ["chrome", "brave", "firefox", "edge", "opera"]))
                    
                    if is_browser:
                        acts.extend(parse_chrome_tabs(web_bucket))
                    else:
                        activity_str = None
                        # 1. Check direct app overrides
                        for key, value in config.get("apps", {}).items():
                            if key in app_name:
                                activity_str = value
                                break
                        
                        # 2. Check categories
                        if not activity_str:
                            for cat_name, cat_data in config.get("categories", {}).items():
                                if any(a in app_name for a in cat_data.get("apps", [])):
                                    activity_str = cat_data.get("display")
                                    break
                                    
                        if activity_str:
                            acts.append(activity_str)
                            
        return acts, is_afk
    except Exception as e:
        print(f"AW error: {e}")
        return None, False

def parse_chrome_tabs(web_bucket):
    config = load_config()
    default_str = config.get("default_website", "Doomscrolling the web 📱")
    acts = []
    if not web_bucket:
        return [default_str]
    try:
        events_resp = requests.get(f"{AW_API}/{web_bucket}/events?limit=5", timeout=1)
        if events_resp.status_code == 200:
            events = events_resp.json()
            for e in events:
                if is_event_stale(e, max_age=300):
                    continue
                url = e["data"].get("url", "")
                title = e["data"].get("title", "")
                
                suffixes = [" - YouTube", " - Google Chrome", " - Mozilla Firefox", " - Brave", " - Vivaldi", " - Opera", " - GitHub"]
                clean_title = title
                for s in suffixes:
                    if clean_title.endswith(s):
                        clean_title = clean_title[:-len(s)]
                        
                import re
                clean_title = re.sub(r'^\(\d+\)\s*', '', clean_title)
                clean_title = clean_title.strip()

                act_str = None
                if "youtube.com" in url:
                    yt_cfg = config.get("youtube", {})
                    is_song = is_youtube_song(url, clean_title)
                    if is_song:
                        if yt_cfg.get("show_songs", True):
                            act_str = yt_cfg.get("song_status", "Listening: {title} 🎵")
                    else:
                        if yt_cfg.get("show_videos", True):
                            act_str = yt_cfg.get("video_status", "Watching: {title} 🍿")
                
                if not act_str:
                    for domain, cfg_str in config.get("websites", {}).items():
                        if domain in url:
                            act_str = cfg_str
                            break
                            
                if not act_str:
                    for cat_name, cat_data in config.get("categories", {}).items():
                        if any(domain in url for domain in cat_data.get("websites", [])):
                            act_str = cat_data.get("display")
                            break
                            
                if not act_str:
                    act_str = default_str
                    
                if "{title}" in act_str:
                    act_str = act_str.replace("{title}", clean_title)
                    
                if act_str not in acts:
                    acts.append(act_str)
                    
            return acts if acts else [default_str]
    except Exception as e:
        print("parse_chrome_tabs error:", e)
    return [default_str]

def fetch_mpris():
    acts = []
    try:
        # Get all mpris players
        out = subprocess.getoutput("busctl --user list | grep org.mpris.MediaPlayer2 || true")
        for line in out.splitlines():
            parts = line.split()
            if not parts or not parts[0].startswith("org.mpris.MediaPlayer2."):
                continue
                
            player = parts[0]
            # Check playback status
            status = subprocess.getoutput(f"busctl --user get-property {player} /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player PlaybackStatus 2>/dev/null || true")
            if "Playing" not in status:
                continue
                
            # Get metadata
            meta = subprocess.getoutput(f"busctl --user get-property {player} /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player Metadata 2>/dev/null || true")
            
            title = ""
            title_match = re.search(r'"xesam:title"\s+(?:v\s+)?s\s+"([^"]+)"', meta)
            if title_match:
                title = title_match.group(1)
                
            artist = ""
            artist_match = re.search(r'"xesam:artist"\s+(?:v\s+)?as\s+1\s+"([^"]+)"', meta)
            if artist_match:
                artist = artist_match.group(1)
                
            if title:
                if artist:
                    acts.append(f"🎵 Listening: {title} by {artist}")
                else:
                    acts.append(f"🎵 Listening: {title}")
    except Exception as e:
        print(f"MPRIS error: {e}")
        
    return acts

def get_current_status(lanyard_user_id: str, external_act: str = None):
    """Returns (List[Activity String], is_afk)"""
    acts = []
    
    # 0. Try External Activity
    if external_act:
        acts.append(external_act)
    
    # 1. Try Discord/Lanyard first
    lanyard_acts = fetch_lanyard(lanyard_user_id)
    acts.extend(lanyard_acts)
    
    # 2. Try ActivityWatch local
    aw_acts, is_afk = fetch_aw()
    if aw_acts:
        acts.extend(aw_acts)
        
    # 3. Try Local Media (MPRIS) for background browser tabs/players
    mpris_acts = fetch_mpris()
    # Deduplicate in case lanyard already caught spotify
    for ma in mpris_acts:
        if ma not in acts:
            acts.append(ma)
            
    # Filter out empty and deduplicate
    unique_acts = []
    
    # We want MPRIS to take precedence over AW if they are duplicates (MPRIS has better formatting)
    # So let's put MPRIS acts first, then AW acts, then Lanyard.
    # Actually `acts` currently has external, lanyard, aw, mpris. 
    # Let's just process them in reverse so mpris is kept, or just do a smart check.
    
    for a in acts:
        if not a:
            continue
            
        import re
        norm_a = re.sub(r'[^a-zA-Z0-9]', '', a.lower())
        
        is_dup = False
        for i, u in enumerate(unique_acts):
            norm_u = re.sub(r'[^a-zA-Z0-9]', '', u.lower())
            
            # If they are very similar (one is a substring of another)
            if len(norm_a) > 10 and len(norm_u) > 10:
                if norm_a in norm_u or norm_u in norm_a:
                    is_dup = True
                    # Prefer the MPRIS one (which usually has the 🎵 prefix) or the longer one
                    if "🎵" in a and "🎵" not in u:
                        unique_acts[i] = a
                    break
        
        if not is_dup:
            unique_acts.append(a)
            
    return unique_acts, is_afk
