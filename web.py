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
    <script src="https://unpkg.com/split.js/dist/split.min.js"></script>
    <style>
        body {{ font-family: sans-serif; background: #121212; color: #fff; margin: 0; padding: 0; height: 100vh; overflow: hidden; box-sizing: border-box; }}
        *, *:before, *:after {{ box-sizing: inherit; }}
        
        .split {{ height: 100vh; width: 100vw; }}
        .pane {{ float: left; height: 100vh; padding: 1.5rem; overflow-y: auto; background: #1e1e1e; }}
        
        /* Custom Scrollbar for a desktop feel */
        ::-webkit-scrollbar {{ width: 2px; height: 2px; }}
        ::-webkit-scrollbar-track {{ background: #121212; }}
        ::-webkit-scrollbar-thumb {{ background: #444; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #666; }}
        
        /* VS Code style gutters */
        .gutter {{
            float: left;
            height: 100vh;
            background-color: #2d2d2d;
            cursor: col-resize;
            transition: background-color 0.1s ease;
        }}
        .gutter:hover, .gutter:active {{ background-color: #007bff; }}

        h2, h3, h4 {{ margin-top: 0; }}
        input, select, button {{ padding: 0.5rem; margin-top: 0.5rem; width: 100%; box-sizing: border-box; background: #333; color: white; border: 1px solid #444; border-radius: 4px; }}
        button {{ background: #007bff; border: none; cursor: pointer; transition: background 0.2s; }}
        button:hover {{ background: #0056b3; }}
        
        .card {{ background: #222; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; border: 1px solid #333; }}
        .card ul {{ overflow-x: auto; white-space: nowrap; padding-bottom: 0.5rem; }}
        
        textarea {{ width: 100%; height: calc(100vh - 120px); padding: 0.5rem; background: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: 14px; border: 1px solid #444; border-radius: 4px; resize: none; white-space: pre; overflow-wrap: normal; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="split">
        <!-- PANE 1: Configuration -->
        <div id="pane-config" class="pane">
            <h3>Configuration (JSON)</h3>
            <form method="post" action="/update_config">
                <textarea name="config_json" spellcheck="false">{config_json}</textarea>
                <button type="submit">Save Configuration</button>
            </form>
        </div>
        
        <!-- PANE 2: Status Control -->
        <div id="pane-status" class="pane" style="background: #181818;">
            <h2>Control Panel</h2>
            <div class="card">
                <form method="post" action="/update">
                    <label>Manual Override:</label>
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
                        <button type="button" onclick="document.getElementById('about').value=''" style="width: auto; padding: 0 1rem; margin: 0; background: #dc3545;">Clear</button>
                    </div>
                    <button type="submit">Update Status</button>
                </form>
            </div>
            
            <div class="card">
                <h4 style="margin-bottom: 0.5rem; color: #888;">System Info</h4>
                <p style="margin: 0; font-size: 0.9em; color: #aaa;">The daemon checks ActivityWatch every 30 seconds.</p>
            </div>
        </div>

        <!-- PANE 3: Activity Explorer -->
        <div id="pane-activity" class="pane">
            <h3>Activity Explorer</h3>
            <p style="font-size: 0.85em; color: #aaa;">Recently tracked names from ActivityWatch.</p>
            
            <div class="card">
                <h4>Apps</h4>
                <ul style="padding-left: 1.2rem; margin-bottom: 0; font-family: monospace; font-size: 0.9em;">
                    {recent_apps}
                </ul>
            </div>
            
            <div class="card">
                <h4>Websites</h4>
                <ul style="padding-left: 1.2rem; margin-bottom: 0; font-family: monospace; font-size: 0.9em;">
                    {recent_sites}
                </ul>
            </div>
        </div>
    </div>

    <script>
        let storedSizes = localStorage.getItem('split-sizes');
        let initialSizes = storedSizes ? JSON.parse(storedSizes) : [20, 55, 25];

        Split(['#pane-config', '#pane-status', '#pane-activity'], {{
            sizes: initialSizes,
            minSize: [300, 250, 200],
            gutterSize: 2,
            cursor: 'col-resize',
            onDragEnd: function (sizes) {{
                localStorage.setItem('split-sizes', JSON.stringify(sizes));
            }}
        }});
    </script>
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
