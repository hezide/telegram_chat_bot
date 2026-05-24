# Telegram Chat Bridge

A web chat UI that bridges a single Telegram participant via SSE + REST.

---

## Stack

- **Backend** — FastAPI, python-telegram-bot v21, async `getUpdates` polling
- **Frontend** — React, `EventSource` (SSE), `POST /api/send`

---

## Setup

### Tests

```bash
cd backend
python -m pytest app/ -v
```

### Local dev

```bash
# Backend
cd backend
python -m venv venv
# Unix/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
cp .env.example .env        # fill in TELEGRAM_BOT_TOKEN
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Send `/start` from Telegram to begin.

### Docker

```bash
cp backend/.env.example backend/.env   # fill in TELEGRAM_BOT_TOKEN
docker-compose up --build

#To stop the application and clean up containers
docker-compose down
```

Open `http://localhost`.

---

## Architecture

```
Browser          FastAPI              Telegram
  |                 |                     |
  |-- POST /send -->|-- send_message() -->|
  |                 |                     |
  |<-- GET /stream -|<-- getUpdates() ----|
  |    (SSE)        |    (long-poll)      |
```

**`app/state.py`** — `AppState`
Owns all mutable runtime state: the active Telegram chat ID and the set of live SSE queues. Exposes `register_chat`, `unregister_chat`, and `broadcast`. Implements `ChatState` via duck typing.

**`app/telegram/`**
- `TelegramClient` — sends messages to Telegram (`send_message`). Implements `MessageGateway`.
- `TelegramListener` — wraps `getUpdates` long-polling into an async generator of raw updates.
- `ChatHandler` — pure business logic; routes `/start`, `/stop`, and messages to state operations. No Telegram or HTTP imports.
- `start_telegram_worker` — wires the above together into a background `asyncio.Task`; owns the command dispatch map.

**`app/routers/chat.py`**
HTTP contract: `GET /api/stream` (SSE fan-out) and `POST /api/send`. Depends only on `ChatState` and `MessageGateway` protocols via FastAPI `Depends()`.

**`app/interfaces.py`**
`ChatState` and `MessageGateway` Protocols — the contracts that decouple routers and handlers from concrete implementations.

---

## SOLID highlights

- **Dependency Inversion** — routes depend on `ChatState` and `MessageGateway` Protocols, injected via FastAPI `Depends()`
- **Single Responsibility** — state, transport, business logic, and HTTP are separate modules
- **Interface Segregation** — `ChatState` and `MessageGateway` are minimal, focused contracts

---
## Assumptions & trade-offs

- Single Telegram participant — first `/start` wins, others are silently ignored, /stop disconnects it and allows the same or a new client
- Session-only — no message persistence; restart clears state
- SSE over WebSocket:
  - simpler for unidirectional server push
  - `POST /send` handles the other direction
  - easier to test
  - Because "the chat may not be consistent" as per requirements, no need to create a websocket and handle states and reconnection of the same  client 
  - Polling telegram bot: the alternative for polling is to use webhook from telegram. this is more robust and scaleable but will require configuring the server in a non-local environment, routing, firawalls etc..  
    polling keeps a connection open but since we support only a single connection to a telegram client it is fine
  - When multiple frontend clients are connected, they all receive the message from telegram and message from a single 

## Known Issues
- unknown commands (e.g., /foo) fall through to handle_message, which will broadcast them as a regular text message.
- Only text is supported: images/stickers for example will not be forwarded to the client
- Message Idempotency: The backend payload does not include message IDs. The frontend relies on client-side generation (crypto.randomUUID()) for React keys. As a result, network-level duplicate SSE events cannot be   deduplicated by the client. fine for that scale.
- Frontend green dot only lights when /start and not when a message is sent on the first time
