# StreamIt Backend

Backend service for a real-time watch-together platform with rooms, chat, and synchronized playback. This repository contains the Django API and WebSocket server only (no frontend).

## Key Features
- Email/password authentication, guest users, and username enforcement
- Room creation and join flows (public, password, approval-based)
- Room participants with host roles and approval status
- Real-time presence events and viewer counts
- Real-time chat with persistence and room-level enable/disable
- Chat hardening (rate limits with cooldown, duplicate suppression, max length)
- Host moderation (mute, kick, ban) with Redis-backed enforcement
- Host-only playback controls with versioned playback state
- Playback state sync for late joiners and drift correction
- Room lifecycle state machine (CREATED -> LIVE -> GRACE -> EXPIRED)
- Grace period with Redis TTL and host reconnect support
- Public room discovery with Redis-backed viewer counts
- Provider abstraction for search and embed URL resolution (Vidking)
- Per-user watch progress persistence and resume endpoints
- Health and metrics endpoints
- Structured logging and security headers

## Tech Stack
- Python 3.11+ recommended
- Django 5.2
- Django REST Framework
- Django Channels + Daphne (ASGI)
- Redis (channel layer and realtime state)
- PostgreSQL via `DATABASE_URL`
- JWT (SimpleJWT)

## Architecture Overview
StreamIt is a single Django project that serves:
- HTTP APIs for authentication and room lifecycle
- WebSockets for presence, chat, and playback synchronization

HTTP traffic is handled by Django (WSGI/ASGI), while real-time events are handled by Django Channels (ASGI) with Redis for fan-out and realtime state. WebSocket authentication is JWT-based using a custom middleware that validates the token from the query string.

Redis is the realtime authority for:
- Host presence and viewers
- Grace timing (TTL)
- Chat rate limiting, duplicate suppression, and moderation state

The database is the durable authority for:
- Room lifecycle state and metadata
- Playback state and watch progress

## Setup Instructions (Local)
Run from `backend/`:

1) Create and activate a virtual environment.
2) Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3) Run migrations:
   ```bash
   python manage.py migrate
   ```
4) (Recommended) Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
5) Start the development server:
   ```bash
   python manage.py runserver
   ```

## Environment Variables
Loaded from `backend/.env`:

- `DEBUG` (true/false)
- `SECRET_KEY`
- `REDIS_URL` (default local: `redis://127.0.0.1:6379/0`)
- `DATABASE_URL` (example: `postgresql://streamit:streamit@localhost:5432/streamit`)
- `TMDB_API_KEY`

Notes:
- Local `ALLOWED_HOSTS` is configured in development settings for `localhost` and `127.0.0.1`.
- CORS is enabled for `http://localhost:3000` and `http://127.0.0.1:3000`.

## Docker (Optional)
From `backend/`:

```bash
docker compose up --build
```

The compose file provides:
- `web` (ASGI app)
- `redis` (Redis 7)
- `db` (PostgreSQL 15)

Container env overrides point to service DNS (`redis`, `db`).

## Observability
- Structured logging to console with format: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`.
- Metrics endpoint: `GET /metrics` (Prometheus scrape).
- Health endpoint: `GET /api/health/`.

## API Overview
Base path: `/api/` (mirrored under `/api/v1/`).

### Auth
- `POST /api/auth/login/` -> Email/password login, returns JWT access token.
- `POST /api/auth/logout/` -> Session logout.
- `POST /api/auth/guest/` -> Guest login via display name, returns JWT access token.
- `POST /api/auth/guest-login/` -> Guest login with generated username, returns JWT access token.
- `POST /api/auth/set-username/` -> Set username (auth required).

### Rooms
- `POST /api/rooms/create/` -> Create room (public/private + entry mode).
- `POST /api/rooms/join/` -> Join room (password or approval flow).
- `POST /api/rooms/approve/` -> Host approves a pending participant.
- `POST /api/rooms/delete/` -> Host deletes a room.
- `POST /api/rooms/progress/save/` -> Save or update watch progress.
- `GET /api/rooms/progress/get/` -> Retrieve watch progress by room/media.
- `GET /api/rooms/<room_code>/resume/` -> Resume progress for a room.
- `GET /api/rooms/public/` -> Public room discovery (Redis-backed, rate limited).
- `GET /api/rooms/search/?q=<query>&page=<n>` -> Provider search (rate limited).

### Other
- `GET /api/health/` -> Health check.
- `GET /metrics` -> Prometheus metrics.

## Rate Limiting
Endpoints protected with IP-based rate limits:
- `GET /api/rooms/public/` -> `20/m` per IP
- `GET /api/rooms/search/` -> `10/m` per IP

## WebSocket Endpoints
- `ws/room/<room_code>/?token=<JWT>`
- `ws/v1/room/<room_code>/?token=<JWT>`

Token is required for all WebSocket connections (session cookies are not sufficient).

## WebSocket Event Types

### Client -> Server
- `CHAT_MESSAGE`: `{ "type": "CHAT_MESSAGE", "message": "..." }`
- `MUTE_USER`: `{ "type": "MUTE_USER", "user_id": "..." }`
- `KICK_USER`: `{ "type": "KICK_USER", "user_id": "..." }`
- `BAN_USER`: `{ "type": "BAN_USER", "user_id": "..." }`
- `PLAY`: `{ "type": "PLAY", "time": <seconds> }`
- `PAUSE`: `{ "type": "PAUSE", "time": <seconds> }`
- `SEEK`: `{ "type": "SEEK", "time": <seconds> }`
- `PLAYER_EVENT`: `{ "type": "PLAYER_EVENT", "data": { "event": "timeupdate|seeked|pause|ended", "currentTime": <seconds>, "duration": <seconds>, "progress": <percent> } }`
- `SYNC_CHECK`: `{ "type": "SYNC_CHECK", "client_time": <seconds> }`

### Server -> Client
- `USER_JOINED`: `{ "type": "USER_JOINED", "user": "..." }`
- `USER_LEFT`: `{ "type": "USER_LEFT", "user": "..." }`
- `ROOM_PARTICIPANTS`: `{ "type": "ROOM_PARTICIPANTS", "participants": [...], "host": "..." }`
- `HOST_DISCONNECTED`: `{ "type": "HOST_DISCONNECTED", "grace_seconds": <seconds> }`
- `HOST_RECONNECTED`: `{ "type": "HOST_RECONNECTED" }`
- `CHAT_MESSAGE`: `{ "type": "CHAT_MESSAGE", "user": "...", "message": "..." }`
- `CHAT_HISTORY`: `{ "type": "CHAT_HISTORY", "messages": [...] }`
- `PLAYBACK_STATE`: `{ "type": "PLAYBACK_STATE", "is_playing": true|false, "time": <seconds>, "version": <int> }`
- `SYNC_CORRECTION`: `{ "type": "SYNC_CORRECTION", "time": <seconds>, "version": <int> }`
- `ERROR`: `{ "type": "ERROR", "message": "..." }`

## Development Notes
- Async ORM rule: all DB access in WebSocket consumers must be wrapped with `database_sync_to_async`.
- WebSocket auth: JWT is mandatory and must be passed as `?token=<JWT>`.
- Host-only playback: only the room host can emit playback commands or `PLAYER_EVENT`.
- Chat disable behavior: when disabled, `CHAT_MESSAGE` is rejected with an `ERROR` payload.
- Chat hardening: messages over 500 chars, duplicate messages, and rate-limit violations return `ERROR`.
- Chat rate limit: sliding window of 5 messages per 3 seconds with a 10-second cooldown.
- Moderation: mute/ban state is Redis-backed; bans are enforced on connect.
- Playback sync: every successful WebSocket join emits exactly one `PLAYBACK_STATE` message.
- Lifecycle state: room state transitions are explicit and DB-authoritative.
- Grace timing: Redis TTL controls grace; DB records state for durability.
- Provider abstraction: search and embed URL resolution is centralized in `providers/`.
- Watch progress: stored per user, room, and media identity.
- Playback completion: host `PLAYER_EVENT` ended marks progress complete.
- Drift correction: clients can send `SYNC_CHECK`; server responds with `SYNC_CORRECTION` if drift > 2s.

### Maintenance Commands
- `python manage.py expire_rooms` -> Marks GRACE rooms as EXPIRED and clears related Redis keys.

## Security Defaults
- Clickjacking protection: `X_FRAME_OPTIONS = "DENY"`.
- MIME sniffing protection: `SECURE_CONTENT_TYPE_NOSNIFF = True`.
- Basic XSS filter: `SECURE_BROWSER_XSS_FILTER = True`.
- Referrer policy: `SECURE_REFERRER_POLICY = "same-origin"`.
- Cookie security flags are set to `False` for local development.

## Roadmap
For the full multi-phase backend and platform roadmap, see `docs/master-roadmap.md`.

## License
TBD
