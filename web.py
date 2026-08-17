from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import threading
from state import StateManager

app = FastAPI()
state_manager = StateManager()

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Rich Presence Dashboard</title>
    <style>
        body { font-family: sans-serif; padding: 2rem; background: #121212; color: #fff; }
        .container { max-width: 600px; margin: auto; background: #1e1e1e; padding: 2rem; border-radius: 8px; }
        input, select, button { padding: 0.5rem; margin-top: 0.5rem; width: 100%; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
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
            <input type="text" name="about" value="{about_val}">
            <br><br>
            <button type="submit">Update Status</button>
        </form>
        <hr>
        <h3>Current Detected Activity</h3>
        <p><b>{activity}</b> (Since: {start_time})</p>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    s = state_manager.state
    status = s["manual_status"]
    
    html = html_template.format(
        online_sel="selected" if status=="Online" else "",
        afk_sel="selected" if status=="AFK" else "",
        dnd_sel="selected" if status=="DND" else "",
        sleep_sel="selected" if status=="Sleeping" else "",
        about_val=s["custom_about"].replace('"', '&quot;'),
        activity=s["current_activity"] or "None",
        start_time=state_manager.get_elapsed_str(s["activity_start_time"])
    )
    return html

@app.post("/update")
async def update_status(status: str = Form(...), about: str = Form(None)):
    state_manager.set_manual_status(status, about or "")
    return HTMLResponse("Updated! <a href='/'>Go back</a>")
