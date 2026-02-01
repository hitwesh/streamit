# StreamIt

StreamIt is a real-time watch-together platform. It is designed as a **client + server** system where clients join a shared room, see presence updates, chat in real time, and stay synchronized to the host’s playback state.

This repository currently contains the backend implementation (Django + DRF + Channels). A frontend is planned and will consume the HTTP + WebSocket contracts described below.

## What StreamIt Provides
- **Rooms** with multiple entry modes: public, password-protected, or host-approval
- **Roles**: host (authoritative playback control) and participants
- **Realtime presence**: join/leave notifications and participant lists
- **Realtime chat** with persistence and per-room enable/disable
- **Playback synchronization**: host-only `PLAY`/`PAUSE`/`SEEK` plus state sync for late joiners
- **Authentication**: email/password and guest users, with JWT for HTTP and WebSockets

## System Components
### Backend (implemented)
- HTTP API for auth and room lifecycle
- WebSocket gateway for presence/chat/playback events
- Admin panel for operational visibility

### Frontend (planned)
The frontend will:
- Authenticate users (email/password or guest) and store the issued JWT
- Allow creating/joining rooms and handling approval/password flows
- Connect to room WebSockets for realtime updates
- Render chat, participant list, and playback state
- For hosts, emit playback commands; for participants, apply received state/events

The backend is intentionally the source of truth for room membership and playback authority; the frontend should be treated as an untrusted client.

## High-Level Architecture
StreamIt uses two communication paths:

1. **HTTP (REST-ish)** for operations that create or change server-side state:
   - login / guest login
   - create room / join room / approve participant

2. **WebSockets (Channels)** for realtime fan-out within a room:
   - presence (`USER_JOINED`, `USER_LEFT`)
   - chat (`CHAT_MESSAGE`, `CHAT_HISTORY`)
   - playback (`PLAY`, `PAUSE`, `SEEK`, and initial `PLAYBACK_STATE` on join)

WebSockets run on Django Channels with **Redis as the channel layer** for broadcasting to room groups.

## Typical Client Flow
1. **Authenticate** via HTTP to obtain an `access_token` (JWT).
2. **Create or join a room** via HTTP.
3. **Connect to WebSocket** for that room:
   - `ws/room/<room_code>/?token=<JWT>`
4. On connect, the server sends:
   - current participant snapshot (`ROOM_PARTICIPANTS`)
   - recent chat history (`CHAT_HISTORY`)
   - current playback state (`PLAYBACK_STATE`)
5. During the session:
   - chat messages are broadcast in real time
   - presence events are broadcast on connect/disconnect
   - only the host’s playback commands are accepted and broadcast

## Technology
- **Backend**: Python, Django 4.2, Django REST Framework
- **Realtime**: Django Channels + Daphne (ASGI)
- **Auth**: JWT via `djangorestframework-simplejwt` (HTTP + WebSockets)
- **Fan-out**: Redis (`channels-redis`)
- **Database**: SQLite for development; PostgreSQL intended for production

## Local Development (Backend)
### Requirements
- Python 3.10+ recommended
- Redis running locally (default `127.0.0.1:6379`)

### Setup
```bash
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver
```

Optional:
```bash
python backend/manage.py createsuperuser
```

Notes:
- The current settings are development-oriented (`DEBUG=True`, SQLite default).
- Redis must be running for WebSocket group messaging.

## Public API Contract (Summary)
Base path: `/api/`

### Auth (HTTP)
- `POST /api/auth/login/` → email/password login; returns `access_token`
- `POST /api/auth/guest/` → guest login; returns `access_token`
- `POST /api/auth/logout/` → logout

### Rooms (HTTP)
- `POST /api/rooms/create/` → create room (public/private + entry mode)
- `POST /api/rooms/join/` → join room (may return `PENDING` for approval rooms)
- `POST /api/rooms/approve/` → host approves pending participant

## WebSocket Contract
Endpoint:

```
ws/room/<room_code>/?token=<JWT>
```

JWT is required for all WebSocket connections; session cookies alone are not sufficient.

### Client → Server Events
- `CHAT_MESSAGE` — `{ "type": "CHAT_MESSAGE", "message": "..." }`
- `PLAY` — `{ "type": "PLAY", "time": <seconds> }`
- `PAUSE` — `{ "type": "PAUSE", "time": <seconds> }`
- `SEEK` — `{ "type": "SEEK", "time": <seconds> }`

### Server → Client Events
- `USER_JOINED` — `{ "type": "USER_JOINED", "user": "..." }`
- `USER_LEFT` — `{ "type": "USER_LEFT", "user": "..." }`
- `ROOM_PARTICIPANTS` — `{ "type": "ROOM_PARTICIPANTS", "participants": [...], "host": "..." }`
- `CHAT_MESSAGE` — `{ "type": "CHAT_MESSAGE", "user": "...", "message": "..." }`
- `CHAT_HISTORY` — `{ "type": "CHAT_HISTORY", "messages": [...] }`
- `PLAYBACK_STATE` — `{ "type": "PLAYBACK_STATE", "is_playing": true|false, "time": <seconds> }`
- `ERROR` — `{ "type": "ERROR", "message": "..." }`

## Development Rules (Important)
- **Async/DB safety**: No ORM access directly inside async WebSocket handlers; use `database_sync_to_async`.
- **Authority model**: Playback is **host-only**. Non-host playback commands are ignored (no broadcast, no error).
- **Chat control**: If a room has chat disabled, chat attempts return an `ERROR` payload.
- **State on join**: Every successful WebSocket join emits exactly one `PLAYBACK_STATE` message.

## Roadmap
- Frontend application (room UI, player integration, chat, presence)
- PostgreSQL support and production configuration
- Containerized local development (Docker + Redis + DB)
- Provider integrations for media metadata and link parsing
- Rate limiting, moderation tooling, and audit logs
- Expanded automated testing (unit + integration)

## Additional Documentation
- Backend-focused details: see `backend/README.md`
- Architecture notes: see `backend/architecture.md`
- Behavioral change log: see `backend/CHANGELOG.md`

## License
TBD
