# app/telegram/worker.py
import asyncio
import logging
from telegram import Bot
from app.telegram.listener import TelegramListener
from app.telegram.handlers import ChatHandler
from app.interfaces import ChatState, MessageGateway

logger = logging.getLogger(__name__)

async def start_telegram_worker(bot_token: str, app_state: ChatState, gateway: MessageGateway) -> asyncio.Task:
    bot = Bot(token=bot_token)
    listener = TelegramListener(bot)
    handler = ChatHandler()

    COMMAND_MAP = {
        "/start": handler.handle_start_command,
        "/stop": handler.handle_stop_command,
    }

    async def polling_loop():
        try:
            async for update in listener.listen():
                msg = update.effective_message
                if not msg or not msg.text:
                    continue

                text = msg.text.strip()

                if text.startswith("/"):
                    command = text.split()[0]
                    if command in COMMAND_MAP:
                        reply = await COMMAND_MAP[command](update, app_state)
                        if reply:
                            await gateway.send_message(msg.chat_id, reply)
                        continue

                reply = await handler.handle_message(update, app_state)
                if reply:
                    await gateway.send_message(msg.chat_id, reply)

        except asyncio.CancelledError:
            listener.stop()
            raise

    return asyncio.create_task(polling_loop())