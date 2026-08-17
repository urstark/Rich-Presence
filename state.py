import json
import time
import os
from typing import Dict, Any

HISTORY_FILE = "history.json"

class StateManager:
    def __init__(self):
        self.state = {
            "manual_status": "Online", # Online, AFK, DND, Sleeping
            "custom_about": "",
            "current_activity": None, 
            "activity_start_time": None,
            "last_pc_active_time": time.time(),
            "history": [] # list of past activities
        }
        self.load_history()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    data = json.load(f)
                    self.state["history"] = data.get("history", [])
                    self.state["manual_status"] = data.get("manual_status", "Online")
                    self.state["custom_about"] = data.get("custom_about", "")
            except Exception as e:
                print(f"Failed to load history: {e}")

    def save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump({
                "history": self.state["history"],
                "manual_status": self.state["manual_status"],
                "custom_about": self.state["custom_about"]
            }, f)

    def set_manual_status(self, status: str, about: str):
        self.state["manual_status"] = status
        self.state["custom_about"] = about
        self.save_history()

    def update_activity(self, activity_text: str, is_afk: bool = False):
        current_time = time.time()
        
        if not is_afk:
            self.state["last_pc_active_time"] = current_time

        # Check for auto-sleep (30 mins = 1800 seconds)
        if current_time - self.state["last_pc_active_time"] > 1800:
            if self.state["manual_status"] != "Sleeping":
                self.state["manual_status"] = "Sleeping"
                self.save_history()
            return "Sleeping", current_time

        if self.state["manual_status"] == "Sleeping":
            # Woke up!
            if not is_afk:
                self.state["manual_status"] = "Online"
                self.save_history()

        # If activity changed
        if activity_text != self.state["current_activity"]:
            if self.state["current_activity"] is not None:
                # push old activity to history
                duration = current_time - (self.state["activity_start_time"] or current_time)
                if duration > 60: # only save if it lasted more than 1 min
                    self.add_to_history(self.state["current_activity"], duration)
            
            self.state["current_activity"] = activity_text
            self.state["activity_start_time"] = current_time

        return self.state["current_activity"], self.state["activity_start_time"]

    def add_to_history(self, activity: str, duration_sec: float):
        if not activity or activity in ["Sleeping", "AFK", "Offline"]:
            return
        
        # Add to today's history or just a flat list of recent activities
        entry = {
            "activity": activity,
            "duration": duration_sec,
            "timestamp": time.time()
        }
        self.state["history"].insert(0, entry)
        # Keep only last 50 entries
        self.state["history"] = self.state["history"][:50]
        self.save_history()

    def get_elapsed_str(self, start_time: float) -> str:
        if not start_time:
            return ""
        elapsed = int(time.time() - start_time)
        if elapsed < 60:
            return "just now"
        mins = elapsed // 60
        hrs = mins // 60
        if hrs > 0:
            return f"for {hrs}h {mins % 60}m"
        return f"for {mins}m"
