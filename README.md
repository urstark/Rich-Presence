# Telegram Rich Presence

A completely local, privacy-first Python script that syncs your local PC activity and global Discord Rich Presence to a dedicated Telegram channel. This provides a "Rich Presence" experience for Telegram users without relying on third-party servers, keeping your browsing and usage data secure on your machine.

## Features

*   **100% Local Execution:** Runs entirely on your local machine. No data is sent to external servers other than the official Telegram API.
*   **Privacy First Whitelist:** Only specific, pre-approved applications are sent to Telegram (e.g., VSCodium, Obsidian, Waydroid). Private applications and file managers are completely ignored.
*   **Smart Web Extraction:** Integrates with ActivityWatch to extract specific YouTube video titles or GitHub repositories without exposing your entire browsing history.
*   **Discord Global Sync:** Integrates with the Lanyard API to fetch your cross-device Discord activity (such as listening to Spotify on your phone) and sync it to Telegram.
*   **Auto-Healing Message:** The bot maintains a single message in your Telegram channel to prevent notification spam. If the message is accidentally deleted, the bot will automatically detect this and create a new one.
*   **Local Web Dashboard:** Includes a local HTTP dashboard to manually set your status (Online, AFK, Do Not Disturb, Sleeping) and write a custom "About" message.

## Prerequisites

*   Python 3.8+
*   [ActivityWatch](https://activitywatch.net/) installed and running locally on port 5600.
*   A Telegram Bot Token (from BotFather).
*   A public Telegram Channel where your bot is an Administrator.
*   (Optional) Join the [Lanyard Discord Server](https://discord.gg/lanyard) to enable global Discord syncing.

## Installation

1. Clone this repository to your local machine.
2. Create a virtual environment and install the dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   *(Note: You can install `fastapi`, `uvicorn`, `requests`, and `python-dotenv` manually if you do not have a requirements.txt)*

3. Create a `.env` file in the root directory with the following variables:
   ```env
   TELEGRAM_BOT_TOKEN="your_bot_token_here"
   TELEGRAM_CHANNEL_ID="-10025******"
   TELEGRAM_MESSAGE_ID=0
   LANYARD_USER_ID="your_discord_id_here"
   ```

## Usage

1. Start the script:
   ```bash
   python main.py
   ```
2. The bot will automatically post a new message to your Telegram channel and update your `.env` file with the `TELEGRAM_MESSAGE_ID`. It will continuously edit this single message to reflect your current status.
3. Open `http://127.0.0.1:5000` in your web browser to access the manual status control dashboard.

## Customizing the Whitelist

To add or remove allowed applications, edit the `WHITELIST` dictionary inside `activity.py`. Only applications listed here will have their activity pushed to Telegram.

## Developer

Developed by **stark**
*   GitHub: [stark](https://github.com/stark)
*   Portfolio: [stark.dev](https://urstark.is-a.dev)

## License

This project is open-source and available under the [GNU General Public License (GPL)](LICENSE).
