import pytest
import asyncio
from app.state import AppState
from app.models import BroadcastEvent, EventType


@pytest.fixture
def app_state():
    """Fresh AppState instance for each test."""
    return AppState()


class TestRegisterChat:
    """register_chat atomically registers the first chat and rejects others."""

    async def test_register_chat_on_first_call(self, app_state):
        """First chat registration succeeds."""
        result = await app_state.register_chat(12345)
        assert result is True
        assert app_state.active_chat_id == 12345

    async def test_register_chat_returns_true_for_same_chat(self, app_state):
        """Same chat ID returns True."""
        await app_state.register_chat(12345)
        result = await app_state.register_chat(12345)
        assert result is True

    async def test_register_chat_returns_false_for_different_chat(self, app_state):
        """Different chat ID returns False and preserves original."""
        await app_state.register_chat(12345)
        result = await app_state.register_chat(67890)
        assert result is False
        assert app_state.active_chat_id == 12345

    async def test_register_chat_concurrent_calls_one_wins(self, app_state):
        """Concurrent calls to register_chat: first wins, others fail."""
        results = await asyncio.gather(
            app_state.register_chat(111),
            app_state.register_chat(222),
            app_state.register_chat(111),
        )
        # One should be True, others False or True if same as first
        assert sum(1 for r in results if r) >= 1
        assert app_state.active_chat_id in (111, 222)


class TestQueueManagement:
    """add_queue and remove_queue manage SSE client queues."""

    async def test_add_queue_lifecycle(self, app_state):
        """add_queue and remove_queue work correctly."""
        q1 = asyncio.Queue()
        q2 = asyncio.Queue()

        await app_state.add_queue(q1)
        await app_state.add_queue(q2)
        await app_state.remove_queue(q1)

        assert q2 in app_state._sse_queues
        assert q1 not in app_state._sse_queues

    async def test_remove_queue_idempotent(self, app_state):
        """Removing same queue twice doesn't raise."""
        q = asyncio.Queue()
        await app_state.add_queue(q)
        await app_state.remove_queue(q)
        await app_state.remove_queue(q)  # Second remove is the no-op being tested
        assert q not in app_state._sse_queues


class TestBroadcast:
    """broadcast delivers events to all active queues."""

    async def test_broadcast_delivers_to_all_queues(self, app_state):
        """Broadcast puts event in all registered queues."""
        q1 = asyncio.Queue()
        q2 = asyncio.Queue()
        await app_state.add_queue(q1)
        await app_state.add_queue(q2)

        event = BroadcastEvent(
            event_type=EventType.MESSAGE,
            text="hello",
            sender="user"
        )
        await app_state.broadcast(event)

        received_q1 = q1.get_nowait()
        received_q2 = q2.get_nowait()

        assert received_q1.text == "hello"
        assert received_q2.text == "hello"

    async def test_broadcast_prunes_full_queues(self, app_state):
        """Broadcast removes queues that are full (max_size exceeded)."""
        q_normal = asyncio.Queue()
        q_full = asyncio.Queue(maxsize=1)

        await q_full.put("something")  # Fill it

        await app_state.add_queue(q_normal)
        await app_state.add_queue(q_full)

        event = BroadcastEvent(
            event_type=EventType.MESSAGE,
            text="test",
            sender="user"
        )
        await app_state.broadcast(event)

        # Normal queue should have the event
        assert await q_normal.get() is event

        # Full queue should have been pruned and not have the event
        # (it still has the old item)
        assert q_full.get_nowait() == "something"

    async def test_broadcast_to_empty_queue_list(self, app_state):
        """Broadcast with no queues doesn't raise."""
        event = BroadcastEvent(
            event_type=EventType.MESSAGE,
            text="test",
            sender="user"
        )
        await app_state.broadcast(event)
        assert app_state._sse_queues == set()


class TestUnregisterChat:
    async def test_unregister_active_chat_returns_true(self, app_state):
        await app_state.register_chat(12345)
        result = await app_state.unregister_chat(12345)
        assert result is True
        assert app_state.active_chat_id is None

    async def test_unregister_clears_active_chat_id(self, app_state):
        await app_state.register_chat(12345)
        await app_state.unregister_chat(12345)
        result = await app_state.register_chat(99999)
        assert result is True
        assert app_state.active_chat_id == 99999

    async def test_unregister_wrong_chat_returns_false(self, app_state):
        await app_state.register_chat(12345)
        result = await app_state.unregister_chat(99999)
        assert result is False
        assert app_state.active_chat_id == 12345

    async def test_unregister_when_no_active_chat_returns_false(self, app_state):
        result = await app_state.unregister_chat(12345)
        assert result is False


class TestActiveChatId:
    """active_chat_id property reflects current state."""

    async def test_active_chat_id_none_initially(self, app_state):
        """active_chat_id is None before any registration."""
        assert app_state.active_chat_id is None

    async def test_active_chat_id_reflects_registration(self, app_state):
        """active_chat_id updates after registration."""
        await app_state.register_chat(999)
        assert app_state.active_chat_id == 999
