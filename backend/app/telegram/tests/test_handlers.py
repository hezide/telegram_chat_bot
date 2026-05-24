from unittest.mock import AsyncMock, MagicMock
from app.telegram.handlers import ChatHandler
from app.interfaces import ChatState
from app.models import EventType


def make_update(chat_id: int = 12345, text: str = "hello") -> MagicMock:
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_message.text = text
    return update


async def test_handle_start_registers_and_broadcasts_system_event():
    state = AsyncMock(spec=ChatState)
    state.register_chat.return_value = True
    handler = ChatHandler()

    reply = await handler.handle_start_command(make_update(), state)

    state.register_chat.assert_called_once_with(12345)
    state.broadcast.assert_called_once()
    event = state.broadcast.call_args[0][0]
    assert event.event_type == EventType.SYSTEM
    assert event.sender == "system"
    assert reply is None


async def test_handle_start_ignored_for_non_active_chat():
    state = AsyncMock(spec=ChatState)
    state.register_chat.return_value = False
    handler = ChatHandler()

    reply = await handler.handle_start_command(make_update(), state)

    state.broadcast.assert_not_called()
    assert reply is not None


async def test_handle_message_broadcasts_to_registered_chat():
    state = AsyncMock(spec=ChatState)
    state.register_chat.return_value = True
    handler = ChatHandler()

    reply = await handler.handle_message(make_update(text="hi there"), state)

    state.broadcast.assert_called_once()
    event = state.broadcast.call_args[0][0]
    assert event.event_type == EventType.MESSAGE
    assert event.text == "hi there"
    assert event.sender == "telegram"
    assert reply is None


async def test_handle_message_ignored_for_non_active_chat():
    state = AsyncMock(spec=ChatState)
    state.register_chat.return_value = False
    handler = ChatHandler()

    reply = await handler.handle_message(make_update(), state)

    state.broadcast.assert_not_called()
    assert reply is not None


async def test_handle_stop_broadcasts_system_event():
    state = AsyncMock(spec=ChatState)
    state.unregister_chat.return_value = True
    handler = ChatHandler()

    await handler.handle_stop_command(make_update(), state)

    state.unregister_chat.assert_called_once_with(12345)
    state.broadcast.assert_called_once()
    event = state.broadcast.call_args[0][0]
    assert event.event_type == EventType.SYSTEM
    assert event.sender == "system"


async def test_handle_stop_ignored_for_non_active_chat():
    state = AsyncMock(spec=ChatState)
    state.unregister_chat.return_value = False
    handler = ChatHandler()

    await handler.handle_stop_command(make_update(), state)

    state.broadcast.assert_not_called()


async def test_handle_message_registers_new_chat_on_first_message():
    state = AsyncMock(spec=ChatState)
    state.register_chat.return_value = True
    handler = ChatHandler()

    await handler.handle_message(make_update(chat_id=99999), state)

    state.register_chat.assert_called_once_with(99999)
