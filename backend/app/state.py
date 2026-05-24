import asyncio
import logging
from typing import Optional
from app.models import BroadcastEvent


logger = logging.getLogger(__name__)


class AppState:
    """
    Manages mutable runtime state for the chat application.
    Implements ChatState Protocol via duck typing.
    """

    def __init__(self):
        self._active_chat_id: Optional[int] = None
        self._sse_queues: set[asyncio.Queue] = set()
        self._chat_id_lock: asyncio.Lock = asyncio.Lock()

    async def register_chat(self, chat_id: int) -> bool:
        """
        Register a Telegram chat. Returns True if this chat is now active,
        False if a different chat was already active.
        """
        async with self._chat_id_lock:
            if self._active_chat_id is None:
                self._active_chat_id = chat_id
                logger.info(f"Active chat registered: {chat_id}")
                return True
            elif self._active_chat_id == chat_id:
                return True
            else:
                logger.info(
                    f"Ignoring chat {chat_id}, already have {self._active_chat_id}"
                )
                return False

    async def unregister_chat(self, chat_id: int) -> bool:
        async with self._chat_id_lock:
            if self._active_chat_id == chat_id:
                self._active_chat_id = None
                logger.info(f"Active chat unregistered: {chat_id}")
                return True
            return False

    async def add_queue(self, q: asyncio.Queue) -> None:
        """Add an SSE client queue to the broadcast list."""
        self._sse_queues.add(q)
        logger.info(f"SSE client connected, total clients: {len(self._sse_queues)}")

    async def remove_queue(self, q: asyncio.Queue) -> None:
        """Remove an SSE client queue from the broadcast list."""
        self._sse_queues.discard(q)
        logger.info(f"SSE client disconnected, total clients: {len(self._sse_queues)}")

    async def broadcast(self, event: BroadcastEvent) -> None:
        """
        Broadcast an event to all connected SSE clients.
        Prunes queues that are full (dead clients).
        """
        dead_queues = []

        for q in self._sse_queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Queue full, pruning dead SSE client")
                dead_queues.append(q)

        for q in dead_queues:
            self._sse_queues.discard(q)

    @property
    def active_chat_id(self) -> Optional[int]:
        """The currently active Telegram chat ID, or None if not yet registered."""
        return self._active_chat_id


# Module-level singleton
_app_state = AppState()
