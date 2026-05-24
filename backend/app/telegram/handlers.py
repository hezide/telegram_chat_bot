import logging
from app.interfaces import ChatState
from app.models import BroadcastEvent, EventType

logger = logging.getLogger(__name__)

_BUSY_MESSAGE = "This bot is already in an active session."


class ChatHandler:
    async def handle_start_command(self, update, app_state: ChatState) -> str | None:
        chat_id = update.effective_chat.id
        registered = await app_state.register_chat(chat_id)
        if registered:
            event = BroadcastEvent(
                event_type=EventType.SYSTEM,
                text="Telegram participant connected",
                sender="system",
            )
            await app_state.broadcast(event)
            logger.info(f"Start command from registered chat {chat_id}")
            return None
        logger.info(f"Rejected /start from non-active chat {chat_id}")
        return _BUSY_MESSAGE

    async def handle_stop_command(self, update, app_state: ChatState) -> str | None:
        chat_id = update.effective_chat.id
        unregistered = await app_state.unregister_chat(chat_id)
        if unregistered:
            event = BroadcastEvent(
                event_type=EventType.SYSTEM,
                text="Telegram participant disconnected",
                sender="system",
            )
            await app_state.broadcast(event)
            logger.info(f"Stop command from chat {chat_id}, session ended")
        else:
            logger.info(f"Ignoring /stop from non-active chat {chat_id}")
        return None

    async def handle_message(self, update, app_state: ChatState) -> str | None:
        chat_id = update.effective_chat.id
        text = update.effective_message.text or ""
        registered = await app_state.register_chat(chat_id)
        if registered:
            event = BroadcastEvent(
                event_type=EventType.MESSAGE,
                text=text,
                sender="telegram",
            )
            await app_state.broadcast(event)
            logger.info(f"Message from {chat_id} broadcast to SSE clients")
            return None
        logger.info(f"Rejected message from non-active chat {chat_id}")
        return _BUSY_MESSAGE
