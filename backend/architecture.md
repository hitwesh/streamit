# Backend Architecture

> This document reflects the backend state as of Feb 20, 2026.
> It will evolve as features are added.

## Overview
StreamIt is a Django 4.2 backend that serves REST APIs and real-time WebSockets for a watch-together platform. Django REST Framework handles HTTP APIs, Django Channels handles WebSockets, and Redis provides realtime authority (presence, viewers, grace TTL, chat moderation/rate limits). The database remains the durable source of truth for room lifecycle and metadata.

## Runtime Stack
- **Django**: Core HTTP handling, ORM, admin, auth.
- **Django REST Framework**: API authentication (JWT).
- **Django Channels + Daphne**: ASGI entry point and WebSocket support.
- **Redis**: Channel layer, presence, viewer counts, grace TTL, chat throttling, and moderation state.
- **SQLite**: Default database (`db.sqlite3`).

## Project Layout
- **core/**: Project configuration and routing.
  - `settings.py`: Apps, auth backends, REST/JWT settings, channel layers.
  - `urls.py`: HTTP API routing (`/api/auth/`, `/api/rooms/`).
  - `asgi.py`: ASGI app with HTTP + WebSocket routing and JWT middleware.
  - `routing.py`: WebSocket URL patterns.
- **users/**: Custom user model and authentication endpoints.
- **rooms/**: Room lifecycle, participants, HTTP APIs, and lifecycle management.
  - `management/commands/expire_rooms.py`: Deterministic room expiry and Redis cleanup.
- **sync/**: WebSocket consumer logic and JWT middleware.
- **chat/**: Chat persistence model and chat history retrieval.
- **common/**: Redis client and canonical Redis key helpers.
- **providers/**: PlaybackSource abstraction and provider resolvers.
  - `base.py`: PlaybackSource contract.
  - `vidking.py`: Vidking source builder and embed URL derivation.
  - `resolver.py`: Canonical entry point for provider resolution.

## Authentication & Authorization
- **User model**: `users.User` (UUID primary key) supports guests (`is_guest=True`).
- **Auth backend**: `users.auth_backends.EmailAuthBackend` for email/password auth.
- **HTTP auth**:
  - `/api/auth/login/` creates a session and returns JWT.
  - `/api/auth/guest/` creates a guest user and returns JWT.
  - `/api/auth/logout/` clears the session.
- **Rooms HTTP**:
  - `create/join/approve` use session auth (`login_required`).
  - `delete` uses DRF + JWT (`IsAuthenticated`).
- **WebSockets**: JWT passed via query string (`?token=...`) and validated in `sync.jwt_middleware.JWTAuthMiddleware`.

## Room Lifecycle (DB Authority)
Rooms use an explicit lifecycle state machine:
- **CREATED → LIVE → GRACE → EXPIRED**
- **Any state → DELETED** (explicit host deletion)

Transition helpers live on the `Room` model and enforce valid transitions only. `host_disconnected_at` is retained as a durability/audit marker, while grace timing is enforced via Redis TTL.

### Grace Timing (Redis Authority)
- Host disconnect triggers:
  - DB: `Room.mark_grace()`
  - Redis: `room:{code}:grace` key with TTL
- Host reconnect clears the grace key and returns room to LIVE.
- Lazy expiry: if a join occurs and the grace TTL key is missing while the DB is GRACE, the room is marked EXPIRED and the connection is closed.

### Lifecycle Enforcement Command
`python manage.py expire_rooms`:
- Finds GRACE rooms past their grace deadline.
- Marks them EXPIRED in the DB.
- Best-effort cleanup of Redis keys (state, host status, participants, grace key).

## Redis Keyspace (Canonical)
- `room:{code}:state` → cached room state payload
- `room:{code}:host_status` → host connection status
- `room:{code}:participants` → set of participant display names
- `room:{code}:viewers` → active socket count
- `room:{code}:grace` → grace TTL key (authoritative timing)
- `room:{code}:chat_rate_window:{user_id}` → sliding window chat rate limiting
- `room:{code}:chat_cooldown:{user_id}` → chat cooldown enforcement
- `room:{code}:chat_dup:{user_id}` → duplicate message suppression window
- `room:{code}:muted_users` → muted user IDs
- `room:{code}:banned_users` → banned user IDs

## HTTP API Surface
### Auth
- `POST /api/auth/login/` → email/password login, returns JWT.
- `POST /api/auth/logout/` → session logout.
- `POST /api/auth/guest/` → guest login, returns JWT.

### Rooms
- `POST /api/rooms/create/` → create room (public/private + entry mode). Returns `room_password` once for private/password rooms.
- `POST /api/rooms/join/` → join room (password or approval flow). Returns `status` (`PENDING`/`APPROVED`) and `is_host`.
- `POST /api/rooms/approve/` → host approves a pending participant by `room_id` and `user_id`.
- `POST /api/rooms/delete/` → host deletes a room.
- `POST /api/rooms/progress/save/` → save or update watch progress (user-scoped).
- `GET /api/rooms/progress/get/` → fetch watch progress by room/media identity.
- `GET /api/rooms/<room_code>/resume/` → resume watch progress by room code.
- `GET /api/rooms/public/` → public room discovery (Redis-backed).

## Public Room Discovery (Redis-Backed)
Public listing filters rooms by:
- DB: `is_private=False`, `is_active=True`, `state=LIVE`
- Redis: host status must be `connected`

Viewer counts are derived from Redis `room:{code}:viewers` and reflect active sockets.

## Real-Time Sync (WebSockets)
- **Endpoint**: `ws/room/<room_code>/?token=<JWT>`
- **Consumer**: `sync.consumers.RoomPresenceConsumer`
  - Validates: authenticated user, room exists, participant approved.
  - Bans are enforced on connect; banned users cannot reconnect.
  - Joins group `room_<code>` and emits presence events (`USER_JOINED`, `USER_LEFT`).
  - Increments viewer count on successful connect; decrements on disconnect.
  - Broadcasts room events
    - `CHAT_MESSAGE` → everyone
    - `PLAYBACK_STATE` → host-only snapshot broadcast (versioned)
  - Sends `PLAYBACK_STATE` on join for sync.
  - Chat can be disabled per room (`is_chat_enabled`), returning an `ERROR` payload when disabled.
  - Chat hardening: 500-char max, sliding-window rate limiting with cooldown, and duplicate suppression (errors only).
  - Chat history on connect returns the most recent 50 messages; storage is capped at 500.
  - Host moderation: `MUTE_USER`, `KICK_USER`, `BAN_USER` (Redis-backed).
  - Host disconnects emit `HOST_DISCONNECTED` with grace seconds; reconnects emit `HOST_RECONNECTED`.
  - Drift correction: clients can send `SYNC_CHECK` and receive `SYNC_CORRECTION` when drift > 2s.
  - `PLAYER_EVENT` from host updates watch progress (ended -> complete).

## PlaybackSource Abstraction
Provider integration is centralized under `providers/` and is backend-only:
- `PlaybackSource` defines provider, media type, external ID, optional season/episode, and capabilities.
- `resolve_playback_source(...)` returns a normalized PlaybackSource.
- `derive_embed_url(...)` returns provider-specific embed URLs.

This keeps provider logic isolated from rooms, Redis, and lifecycle logic.


## Data Model
### User
- UUID primary key.
- Email + password (optional for guests).
- `display_name`, `is_guest`, `is_staff`, `is_superuser`.
- `last_seen`, `created_at` timestamps.

### Room
- UUID primary key, unique `code`.
- Host: FK to `User`.
- Lifecycle: `state` (CREATED, LIVE, GRACE, EXPIRED, DELETED).
- Privacy: `is_private`, `entry_mode` (APPROVAL or PASSWORD).
- Optional hashed entry password (auto-generated 8-char password, shown once).
- Media fields: `video_provider`, `video_id`.
- `is_chat_enabled`, `is_active`, `host_disconnected_at`.
- Grace duration: `GRACE_PERIOD_SECONDS`.

### RoomPlaybackState
- One-to-one with Room.
- `is_playing`, `current_time`, `updated_at`.
- `version` increments on every host playback change.

### RoomParticipant
- FK to `Room` and `User`.
- `status`: `PENDING` or `APPROVED`.
- `joined_at`, `last_heartbeat`.
- Unique constraint on (`room`, `user`).

### WatchProgress
- FK to `User` and `Room`.
- Media identity: `media_id`, `media_type`, optional `season`, `episode`.
- Progress: `timestamp`, `duration`, `progress_percent`, `completed`.
- Unique constraint on (`user`, `room`, `media_id`, `season`, `episode`).

### ChatMessage
- FK to `Room` and `User`.
- `message`, `created_at`.
- Persisted and read for `CHAT_HISTORY` on join.

## Request/Message Flow Summary
1. **Login** via HTTP API → session + JWT returned.
2. **Create/Join room** via HTTP API → participant created/approved (or pending).
3. **Connect to WebSocket** with `?token=` → consumer validates participant.
4. **Presence + events** flow via channel layer to all room members.

## Constraints
- Async ORM access is prohibited in WebSocket handlers; all DB access must be wrapped in `database_sync_to_async`.
- Redis is realtime authority; DB is durable authority.
- Public discovery has no side effects on read.
- Chat enforcement and moderation are Redis-only (no DB writes).

## Notes / TODO Candidates
- Add production `ALLOWED_HOSTS` and environment-based settings.
- Consider PostgreSQL for production.
- Add rate limiting and audit logs for room events.
