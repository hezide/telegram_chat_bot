import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.telegram.listener import TelegramListener


def make_update(update_id: int) -> MagicMock:
    u = MagicMock()
    u.update_id = update_id
    return u


async def test_listen_yields_updates():
    bot = AsyncMock()
    listener = TelegramListener(bot=bot)
    u1, u2 = make_update(1), make_update(2)

    calls = 0
    async def get_updates(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return [u1, u2]
        listener.stop()
        return []

    bot.get_updates.side_effect = get_updates
    result = [u async for u in listener.listen()]

    assert result == [u1, u2]


async def test_listen_tracks_offset_correctly():
    bot = AsyncMock()
    listener = TelegramListener(bot=bot)
    offsets_seen = []

    calls = 0
    async def get_updates(offset, **kwargs):
        nonlocal calls
        calls += 1
        offsets_seen.append(offset)
        if calls == 1:
            return [make_update(10), make_update(11)]
        listener.stop()
        return []

    bot.get_updates.side_effect = get_updates
    _ = [u async for u in listener.listen()]

    assert offsets_seen == [0, 12]


async def test_listen_stops_when_stop_called():
    bot = AsyncMock()
    listener = TelegramListener(bot=bot)

    async def get_updates(**kwargs):
        listener.stop()
        return [make_update(1)]

    bot.get_updates.side_effect = get_updates
    result = [u async for u in listener.listen()]

    assert len(result) == 1


async def test_listen_exits_cleanly_on_cancelled_error():
    bot = AsyncMock()
    bot.get_updates.side_effect = asyncio.CancelledError
    listener = TelegramListener(bot=bot)

    result = [u async for u in listener.listen()]

    assert result == []


async def test_listen_retries_after_polling_error():
    bot = AsyncMock()
    listener = TelegramListener(bot=bot)
    u = make_update(5)

    calls = 0
    async def get_updates(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise Exception("Timeout")
        listener.stop()
        return [u]

    bot.get_updates.side_effect = get_updates
    with patch("app.telegram.listener.asyncio.sleep"):
        result = [u async for u in listener.listen()]

    assert result == [u]
    assert calls == 2
