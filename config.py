import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "categories": {
        "Study 📚": {
            "display": "Deep in Study 📖",
            "apps": [],
            "websites": ["pw.live", "pwthor.live"]
        }
    },
    "apps": {
        "codium": "Cooking inside VSCodium 🍳",
        "antigravity": "Cooking smth in VSCodium 🍳",
        "waydroid": "Messing around in Waydroid 📱",
        "obsidian": "Drafting smth in Obsidian 📝",
        "discord": "Shitposting on Discord ☕",
        "telegram": "Using Telegram ☕",
        "ayugram": "Using Telegram ☕"
    },
    "websites": {
        "github.com": "Exploring GitHub: {title} 👀",
        "reddit.com": "Scrolling Reddit 👾",
        "instagram.com": "Scrolling Instagram",
        "snapchat.com": "Snapping 👻",
        "twitter.com": "Arguing on Twitter 🐦",
        "threads.net": "Reading Threads 📱"
    },
    "youtube": {
        "show_videos": False,
        "show_songs": True,
        "video_status": "Watching: {title} 🍿",
        "song_status": "Listening: {title} 🎵"
    },
    "browsers": [
        "chrome",
        "brave",
        "firefox",
        "edge",
        "opera"
    ],
    "default_website": "Doomscrolling the web"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
        
    try:
        py_mtime = os.path.getmtime(__file__)
        json_mtime = os.path.getmtime(CONFIG_FILE)
        if py_mtime > json_mtime:
            # User edited config.py directly!
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    except:
        pass

    try:
        with open(CONFIG_FILE, "r") as f:
            curr = json.load(f)
            
        changed = False
        for k, v in DEFAULT_CONFIG.items():
            if k not in curr:
                curr[k] = v
                changed = True
            elif isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    if sub_k not in curr[k]:
                        curr[k][sub_k] = sub_v
                        changed = True
        if changed:
            save_config(curr)
        return curr
    except:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
