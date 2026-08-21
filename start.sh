#!/bin/bash
# Start Telegram Rich Presence

cd "$(dirname "$0")"

# Check if Rich Presence is running on port 5000
if ! nc -z localhost 5000; then
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1

    echo "Starting Rich Presence..."
    nohup python main.py > rich_presence.log 2>&1 &
    sleep 1
fi

xdg-open http://localhost:5000
