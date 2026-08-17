import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "apps": {
        "codium": "Cooking inside VSCodium 🍳",
        "obsidian": "Drafting smth in Obsidian 📝",
        "antigravity": "Cooking smth",
        "waydroid": "Messing around in Waydroid 📱",
        "discord": "Shitposting on Discord 💬",
        "telegram": "Using Telegram",
        "ayugram": "Using Telegram ☕"
    },
    "websites": {
        "youtube.com": "Watching: {title} 🍿",
        "github.com": "Exploring GitHub: {title} 👀",
        "twitter.com": "Arguing on Twitter 🐦",
        "reddit.com": "Scrolling Reddit 👾"
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
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
