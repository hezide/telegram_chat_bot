from unittest.mock import AsyncMock, patch
from app.telegram.client import TelegramClient


async def test_send_message_returns_true_on_success():
    client = TelegramClient()
    client._bot = AsyncMock()

    result = await client.send_message(12345, "hello")

    assert result is True
    client._bot.send_message.assert_called_once_with(chat_id=12345, text="hello")


async def test_send_message_returns_false_on_exception():
    client = TelegramClient()
    client._bot = AsyncMock()
    client._bot.send_message.side_effect = Exception("Network error")

    result = await client.send_message(12345, "hello")

    assert result is False


async def test_bot_initialised_lazily():
    client = TelegramClient()
    assert client._bot is None

    mock_bot = AsyncMock()
    with patch("app.telegram.client.Bot", return_value=mock_bot), \
         patch("app.config.get_bot_token", return_value="fake-token"):
        await client.send_message(12345, "hello")

    assert client._bot is mock_bot
