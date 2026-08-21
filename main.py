import os
import time
import threading
# pyrefly: ignore [missing-import]
import uvicorn
from dotenv import load_dotenv

from web import app, state_manager
from activity import get_current_status
from bot import update_telegram_message

load_dotenv()
LANYARD_ID = os.getenv("LANYARD_USER_ID")

def background_loop():
    while True:
        try:
            # 1. Fetch current activity
            external_act = state_manager.state.get("external_activity")
            act_list, is_afk = get_current_status(LANYARD_ID, external_act)
            
            # 2. Update state manager
            state_manager.update_activity(act_list, is_afk)
            
            # 3. Push to Telegram
            update_telegram_message(state_manager)
            
        except Exception as e:
            print(f"Loop error: {e}")
        
        # Poll every 5 seconds for near-instant updates
        time.sleep(5)

if __name__ == "__main__":
    # Start background thread
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    
    # Start web server on port 5000
    uvicorn.run(app, host="127.0.0.1", port=5000)
