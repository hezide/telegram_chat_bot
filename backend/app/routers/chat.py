import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.interfaces import ChatState, MessageGateway
from app.dependencies import get_app_state, get_message_gateway
from app.models import BroadcastEvent, EventType, SendMessageRequest, SendMessageResponse

router = APIRouter()


@router.get("/stream")
async def stream(state: ChatState = Depends(get_app_state)):
    queue: asyncio.Queue = asyncio.Queue()
    await state.add_queue(queue)

    async def generate():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                    continue
                payload = {
                    "type": event.event_type.value,
                    "text": event.text,
                    "sender": event.sender,
                }
                yield f"event: {event.event_type.value}\ndata: {json.dumps(payload)}\n\n"
        finally:
            await state.remove_queue(queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/send", response_model=SendMessageResponse)
async def send(
    payload: SendMessageRequest,
    state: ChatState = Depends(get_app_state),
    gateway: MessageGateway = Depends(get_message_gateway),
):
    if state.active_chat_id is None:
        raise HTTPException(status_code=409, detail="No active Telegram chat")

    success = await gateway.send_message(state.active_chat_id, payload.text)

    if not success:
        raise HTTPException(status_code=502, detail="Telegram API error")

    await state.broadcast(BroadcastEvent(
        event_type=EventType.MESSAGE,
        text=payload.text,
        sender="user",
    ))
    return SendMessageResponse(ok=True)
