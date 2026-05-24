import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")


def get_bot_token() -> str:
    """Get Telegram bot token from environment. Raises KeyError if not set."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise KeyError(
            "TELEGRAM_BOT_TOKEN not set. Copy .env.example to .env and fill in your token."
        )
    return token
