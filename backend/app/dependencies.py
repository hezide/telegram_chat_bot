from app.state import _app_state
from app.interfaces import ChatState, MessageGateway


async def get_app_state() -> ChatState:
    return _app_state


async def get_message_gateway() -> MessageGateway:
    from app.telegram import _telegram_client
    return _telegram_client
