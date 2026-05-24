import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_app_state, get_message_gateway
from app.interfaces import ChatState, MessageGateway


def make_mock_state(active_chat_id=None) -> AsyncMock:
    state = AsyncMock(spec=ChatState)
    state.active_chat_id = active_chat_id
    return state


def make_mock_gateway(success=True) -> AsyncMock:
    gateway = AsyncMock(spec=MessageGateway)
    gateway.send_message.return_value = success
    return gateway


def test_send_success():
    state = make_mock_state(active_chat_id=12345)
    gateway = make_mock_gateway(success=True)
    app.dependency_overrides[get_app_state] = lambda: state
    app.dependency_overrides[get_message_gateway] = lambda: gateway

    try:
        with TestClient(app) as client:
            response = client.post("/api/send", json={"text": "hello"})
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        gateway.send_message.assert_called_once_with(12345, "hello")
        state.broadcast.assert_called_once()
        event = state.broadcast.call_args[0][0]
        assert event.sender == "user"
        assert event.text == "hello"
    finally:
        app.dependency_overrides.clear()


def test_send_no_active_chat():
    state = make_mock_state(active_chat_id=None)
    gateway = make_mock_gateway()
    app.dependency_overrides[get_app_state] = lambda: state
    app.dependency_overrides[get_message_gateway] = lambda: gateway

    try:
        with TestClient(app) as client:
            response = client.post("/api/send", json={"text": "hello"})
        assert response.status_code == 409
        gateway.send_message.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_send_blank_text():
    state = make_mock_state(active_chat_id=12345)
    gateway = make_mock_gateway()
    app.dependency_overrides[get_app_state] = lambda: state
    app.dependency_overrides[get_message_gateway] = lambda: gateway

    try:
        with TestClient(app) as client:
            response = client.post("/api/send", json={"text": "   "})
        assert response.status_code == 422
        gateway.send_message.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_send_telegram_failure():
    state = make_mock_state(active_chat_id=12345)
    gateway = make_mock_gateway(success=False)
    app.dependency_overrides[get_app_state] = lambda: state
    app.dependency_overrides[get_message_gateway] = lambda: gateway

    try:
        with TestClient(app) as client:
            response = client.post("/api/send", json={"text": "hello"})
        assert response.status_code == 502
        state.broadcast.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_stream_returns_event_stream_content_type():
    state = make_mock_state()
    app.dependency_overrides[get_app_state] = lambda: state

    with patch("app.routers.chat.asyncio.wait_for", side_effect=asyncio.CancelledError):
        try:
            with TestClient(app) as client:
                with client.stream("GET", "/api/stream") as response:
                    assert response.status_code == 200
                    assert "text/event-stream" in response.headers["content-type"]
                    state.add_queue.assert_called_once()
        finally:
            app.dependency_overrides.clear()


def test_stream_removes_queue_on_disconnect():
    state = make_mock_state()
    app.dependency_overrides[get_app_state] = lambda: state

    with patch("app.routers.chat.asyncio.wait_for", side_effect=asyncio.CancelledError):
        try:
            with TestClient(app) as client:
                with client.stream("GET", "/api/stream") as response:
                    assert response.status_code == 200

            state.remove_queue.assert_called_once()
        finally:
            app.dependency_overrides.clear()
