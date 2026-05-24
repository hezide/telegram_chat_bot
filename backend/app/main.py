import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGIN, get_bot_token
from app.routers.chat import router as chat_router
from app.dependencies import get_app_state
from app.interfaces import ChatState
from app.state import _app_state
from app.telegram import _telegram_client
from app.telegram.worker import start_telegram_worker

logging.basicConfig(
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = await start_telegram_worker(
        bot_token=get_bot_token(),
        app_state=_app_state,
        gateway=_telegram_client,
    )
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Telegram background worker fully terminated")


app = FastAPI(title="Telegram Chat Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router, prefix="/api")


@app.get("/health")
async def health(state: ChatState = Depends(get_app_state)):
    return {"status": "ok", "active_chat_id": state.active_chat_id}
