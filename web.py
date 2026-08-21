# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request, Form
# pyrefly: ignore [missing-import]
from fastapi.responses import HTMLResponse, RedirectResponse
import threading
import json
from state import StateManager
from config import load_config, save_config

app = FastAPI()
state_manager = StateManager()


def get_recent_aw_items():
    import requests
    apps = set()
    websites = set()
    try:
        resp = requests.get("http://localhost:5600/api/0/buckets", timeout=1)
        if resp.status_code == 200:
            buckets = resp.json()
            window = next((k for k in buckets.keys() if "aw-watcher-window" in k), None)
            web = next((k for k in buckets.keys() if "aw-watcher-web" in k), None)
            
            if window:
                events = requests.get(f"http://localhost:5600/api/0/buckets/{window}/events?limit=50", timeout=1).json()
                for e in events:
                    if "app" in e.get("data", {}):
                        apps.add(e["data"]["app"])
                        
            if web:
                events = requests.get(f"http://localhost:5600/api/0/buckets/{web}/events?limit=50", timeout=1).json()
                for e in events:
                    if "url" in e.get("data", {}):
                        try:
                            domain = e["data"]["url"].split("/")[2]
                            websites.add(domain)
                        except:
                            pass
    except:
        pass
    return sorted(list(apps)), sorted(list(websites))

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    s = state_manager.state
    status = s["manual_status"]
    
    config = load_config()
    apps, sites = get_recent_aw_items()
    
    apps_html = "".join(f"<li>{a}</li>" for a in apps) or "<li>No recent apps</li>"
    sites_html = "".join(f"<li>{s}</li>" for s in sites) or "<li>No recent websites</li>"
    
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    html = html.replace('{online_sel}', "selected" if status=="Online" else "")
    html = html.replace('{afk_sel}', "selected" if status=="AFK" else "")
    html = html.replace('{dnd_sel}', "selected" if status=="DND" else "")
    html = html.replace('{sleep_sel}', "selected" if status=="Sleeping" else "")
    html = html.replace('{about_val}', s["custom_about"].replace('"', '&quot;'))
    html = html.replace('{config_json}', json.dumps(config, indent=4))
    html = html.replace('{recent_apps}', apps_html)
    html = html.replace('{recent_sites}', sites_html)
    
    return html

@app.post("/update")
async def update_status(status: str = Form(...), about: str = Form(None)):
    state_manager.set_manual_status(status, about or "")
    return RedirectResponse(url="/", status_code=303)

@app.post("/update_config")
async def update_config(config_json: str = Form(...)):
    try:
        new_config = json.loads(config_json)
        save_config(new_config)
    except Exception as e:
        print(f"Failed to save config: {e}")
    return RedirectResponse(url="/", status_code=303)

# pyrefly: ignore [missing-import]
from pydantic import BaseModel

class ExternalStatusRequest(BaseModel):
    activity: str

@app.post("/api/external_status")
async def update_external_status(req: ExternalStatusRequest):
    """
    Endpoint for external trackers to push their status.
    Send an empty string to clear the external activity.
    """
    state_manager.set_external_activity(req.activity)
    return {"status": "success", "external_activity": req.activity}

@app.post("/api/shutdown")
async def shutdown_server():
    import os
    import time
    def kill_soon():
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=kill_soon).start()
    return HTMLResponse("<h2>Server is shutting down... You can close this tab.</h2><script>setTimeout(()=>window.close(), 2000);</script>")
