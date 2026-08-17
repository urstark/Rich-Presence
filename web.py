from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import threading
import json
from state import StateManager
from config import load_config, save_config

app = FastAPI()
state_manager = StateManager()

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Rich Presence Dashboard</title>
    <style>
        body {{ font-family: sans-serif; padding: 2rem; background: #121212; color: #fff; }}
        .container {{ max-width: 600px; margin: auto; background: #1e1e1e; padding: 2rem; border-radius: 8px; }}
        input, select, button {{ padding: 0.5rem; margin-top: 0.5rem; width: 100%; box-sizing: border-box; }}
        button {{ background: #007bff; color: white; border: none; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Rich Presence Control</h2>
        <form method="post" action="/update">
            <label>Status:</label>
            <select name="status">
                <option value="Online" {online_sel}>Online</option>
                <option value="AFK" {afk_sel}>AFK</option>
                <option value="DND" {dnd_sel}>Do Not Disturb</option>
                <option value="Sleeping" {sleep_sel}>Sleeping</option>
            </select>
            <br><br>
            <label>Custom About Text:</label>
            <div style="display: flex; gap: 10px; margin-top: 0.5rem; margin-bottom: 1rem;">
                <input type="text" id="about" name="about" value="{about_val}" style="margin: 0;">
                <button type="button" onclick="document.getElementById('about').value=''" style="width: auto; padding: 0 1.5rem; margin: 0; background: #dc3545;">Clear</button>
            </div>
            <button type="submit">Update Status</button>
        </form>
        <hr>
        <h3>Whitelist Configuration (JSON)</h3>
        <form method="post" action="/update_config">
            <textarea name="config_json" rows="12" style="width: 100%; padding: 0.5rem; background: #333; color: #fff; font-family: monospace; box-sizing: border-box; border: 1px solid #555; border-radius: 4px;">{config_json}</textarea>
            <button type="submit">Save Configuration</button>
        </form>
        
        <hr>
        <h3>Recently Tracked Activity</h3>
        <p style="font-size: 0.9em; color: #aaa;">Use these names in your configuration above to track them.</p>
        <div style="display: flex; gap: 20px; font-family: monospace;">
            <div style="flex: 1; background: #222; padding: 1rem; border-radius: 4px;">
                <h4 style="margin-top: 0;">Apps</h4>
                <ul style="padding-left: 1.2rem; margin-bottom: 0;">
                    {recent_apps}
                </ul>
            </div>
            <div style="flex: 1; background: #222; padding: 1rem; border-radius: 4px;">
                <h4 style="margin-top: 0;">Websites</h4>
                <ul style="padding-left: 1.2rem; margin-bottom: 0;">
                    {recent_sites}
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""

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
    
    html = html_template.format(
        online_sel="selected" if status=="Online" else "",
        afk_sel="selected" if status=="AFK" else "",
        dnd_sel="selected" if status=="DND" else "",
        sleep_sel="selected" if status=="Sleeping" else "",
        about_val=s["custom_about"].replace('"', '&quot;'),
        config_json=json.dumps(config, indent=4),
        recent_apps=apps_html,
        recent_sites=sites_html
    )
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
