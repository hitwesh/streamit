# StreamIt Backend

Backend service for a real-time watch-together platform with rooms, chat, and synchronized playback. This repository contains the Django 4.2 API and WebSocket server only (no frontend).

## Key Features
- Email/password authentication and guest users
- Room creation and join flows (public, password, approval-based)
- Room participants with host roles
- Real-time presence events (`USER_JOINED`, `USER_LEFT`)
- Real-time chat with persistence and room-level enable/disable
- Host-only playback controls (`PLAY`, `PAUSE`, `SEEK`)
- Playback state sync for late joiners
- Room lifecycle state machine (CREATED → LIVE → GRACE → EXPIRED)
- Grace period with Redis TTL and host reconnect support
- Public room discovery with Redis-backed viewer counts
- Provider abstraction for embed URL resolution (Vidking)
- Per-user watch progress persistence
- Admin panel enabled

## Tech Stack
- Python
- Django 4.2
- Django REST Framework
- Django Channels + Daphne (ASGI)
- Redis (channel layer)
- SQLite (development database; PostgreSQL planned)
- JWT (SimpleJWT)

## Architecture Overview
StreamIt is a single Django project that serves:
- **HTTP APIs** for authentication and room lifecycle
- **WebSockets** for presence, chat, and playback synchronization

HTTP traffic is handled by Django (WSGI/ASGI), while real-time events are handled by Django Channels (ASGI) with Redis for fan-out. WebSocket authentication is JWT-based using a custom middleware that validates the token from the query string.

Redis is the realtime authority for:
- Host presence
- Viewer counts
- Grace timing (TTL)

The database is the durable authority for:
- Room lifecycle state
- Room metadata
- Playback state

## Setup Instructions
### Database initialization (first run)

Run these commands **in this exact order** when setting up the backend database.

Run from `backend/`:

```bash
python manage.py makemigrations
python manage.py migrate
```

What each does:
- `makemigrations` → generates migration files (schema intent)
- `migrate` → applies schema to the database

⚠️ Note: this repository already contains migrations. On a fresh setup, running:

```bash
python manage.py migrate
```

is usually enough.

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. (Recommended) Create a superuser (admin):
   ```bash
   python manage.py createsuperuser
   ```
  Notes:
  - This project uses a custom `User` model.
  - Superusers default to `display_name="Admin"` (used in examples and manual testing).
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Environment Requirements
- **Python**: 3.10+ recommended
- **Redis**: running locally (default `127.0.0.1:6379`) for WebSocket fan-out

## API Overview
Base path: `/api/`

### Auth
- `POST /api/auth/login/` → Email/password login, returns JWT
- `POST /api/auth/guest/` → Guest login (`display_name`), returns JWT
- `POST /api/auth/logout/` → Session logout

### Rooms
- `POST /api/rooms/create/` → Create room (public/private + entry mode)
- `POST /api/rooms/join/` → Join room (password or approval flow)
- `POST /api/rooms/approve/` → Host approves a pending participant
- `POST /api/rooms/delete/` → Host deletes a room
- `POST /api/rooms/progress/save/` → Save or update watch progress
- `GET /api/rooms/progress/get/` → Retrieve watch progress by room/media
- `GET /api/rooms/public/` → Public room discovery (Redis-backed)

## WebSocket Endpoint
- `ws/room/<room_code>/?token=<JWT>`

The token is required for all WebSocket connections. Sessions alone are not sufficient.

## WebSocket Event Types

### Client → Server
- `CHAT_MESSAGE`:
  - Payload: `{ "type": "CHAT_MESSAGE", "message": "..." }`
- `PLAY`:
  - Payload: `{ "type": "PLAY", "time": <seconds> }`
- `PAUSE`:
  - Payload: `{ "type": "PAUSE", "time": <seconds> }`
- `SEEK`:
  - Payload: `{ "type": "SEEK", "time": <seconds> }`

### Server → Client
- `USER_JOINED`:
  - Payload: `{ "type": "USER_JOINED", "user": "..." }`
- `USER_LEFT`:
  - Payload: `{ "type": "USER_LEFT", "user": "..." }`
- `ROOM_PARTICIPANTS`:
  - Payload: `{ "type": "ROOM_PARTICIPANTS", "participants": [...], "host": "..." }`
- `HOST_DISCONNECTED`:
  - Payload: `{ "type": "HOST_DISCONNECTED", "grace_seconds": <seconds> }`
- `HOST_RECONNECTED`:
  - Payload: `{ "type": "HOST_RECONNECTED" }`
- `CHAT_MESSAGE`:
  - Payload: `{ "type": "CHAT_MESSAGE", "user": "...", "message": "..." }`
- `CHAT_HISTORY`:
  - Payload: `{ "type": "CHAT_HISTORY", "messages": [...] }`
- `PLAYBACK_STATE`:
  - Payload: `{ "type": "PLAYBACK_STATE", "is_playing": true|false, "time": <seconds> }`
- `ERROR`:
  - Payload: `{ "type": "ERROR", "message": "..." }`

## Development Notes
- **Async ORM rule**: All database access in WebSocket consumers must be wrapped with `database_sync_to_async`.
- **WebSocket auth**: JWT is mandatory and must be passed as `?token=<JWT>`.
- **Host-only playback**: Only the room host can emit `PLAY`, `PAUSE`, and `SEEK`.
- **Chat disable behavior**: When disabled, `CHAT_MESSAGE` is rejected with an `ERROR` payload.
- **Playback sync**: Every successful WebSocket join emits exactly one `PLAYBACK_STATE` message.
- **Lifecycle state**: Room state transitions are explicit and DB-authoritative.
- **Grace timing**: Redis TTL controls grace; DB records state for durability.
- **Provider abstraction**: Embed URL resolution is centralized in `providers/`.
- **Watch progress**: Stored per user, room, and media identity.

### Maintenance Commands
- `python manage.py expire_rooms` → Marks GRACE rooms as EXPIRED and clears related Redis keys.

## Future Roadmap
For the full multi-phase backend and platform roadmap, see `docs/master-roadmap.md`.

Highlights:
- PostgreSQL support for production
- Provider integration for video metadata
- Rate limiting and audit logging for room events
- Expanded test coverage (unit + integration)
- Dockerized development workflow

## License
TBD
