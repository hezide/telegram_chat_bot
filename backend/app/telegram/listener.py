import asyncio
import logging
from typing import AsyncGenerator
from telegram import Bot, Update

logger = logging.getLogger(__name__)


class TelegramListener:
    def __init__(self, bot: Bot):
        self._bot = bot
        self._running = False

    async def listen(self) -> AsyncGenerator[Update, None]:
        self._running = True
        offset = 0
        logger.info("Telegram listener polling started")
        while self._running:
            try:
                updates = await self._bot.get_updates(
                    offset=offset, timeout=30, read_timeout=35, allowed_updates=Update.ALL_TYPES
                )
                for update in updates:
                    offset = update.update_id + 1
                    logger.info(f"Received update {update.update_id}: {update.effective_message and update.effective_message.text!r}")
                    yield update
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(3)
        logger.info("Telegram listener stopped")

    def stop(self):
        self._running = False
