import logging
from typing import Optional
from telegram import Bot

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self):
        self._bot: Optional[Bot] = None

    def _get_bot(self) -> Bot:
        if self._bot is None:
            from app.config import get_bot_token
            self._bot = Bot(token=get_bot_token())
        return self._bot

    async def send_message(self, chat_id: int, text: str) -> bool:
        try:
            await self._get_bot().send_message(chat_id=chat_id, text=text)
            logger.debug(f"Sent message to {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return False


_telegram_client = TelegramClient()
