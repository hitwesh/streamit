# Backend Architecture

Date: January 31, 2026

## Overview
This backend is a Django 4.2 project with Django REST Framework for HTTP APIs and Django Channels (ASGI) for real-time WebSocket communication. Authentication uses a custom `User` model with email/password and guest accounts, a custom email auth backend, plus JWT tokens for API/WebSocket access. WebSockets use Redis as the channel layer backend.

## Runtime Stack
- **Django**: Core HTTP handling, ORM, admin, auth.
- **Django REST Framework**: API authentication (`JWTAuthentication`).
- **Django Channels + Daphne**: ASGI entry point, WebSocket support.
- **Redis**: Channel layer for websocket fan-out (configured at 127.0.0.1:6379).
- **SQLite**: Default database (`db.sqlite3`).

## Project Layout
- **core/**: Project configuration and routing.
  - `settings.py`: Installed apps, auth backends, REST/JWT settings, channel layers.
  - `urls.py`: HTTP API routing (`/api/auth/`, `/api/rooms/`).
  - `asgi.py`: ASGI app with HTTP + WebSocket protocol routing and JWT middleware.
  - `routing.py`: WebSocket URL patterns.
- **users/**: Custom user model and authentication endpoints.
- **rooms/**: Room lifecycle, participants, and approval flow.
- **sync/**: WebSocket consumers and JWT middleware.
- **chat/**, **providers/**, **common/**: Present for future domain features (no models yet).

## Authentication & Authorization
- **User model**: `users.User` (UUID primary key), supports guests (`is_guest=True`).
- **Auth backend**: `users.auth_backends.EmailAuthBackend` enables email/password auth.
- **Login**:
  - `/api/auth/login/` authenticates email/password, creates a session, returns a JWT.
  - `/api/auth/guest/` requires `display_name`, creates a guest user, returns a JWT.
- **WebSockets**: JWT passed via query string (`?token=...`) and validated in `sync.jwt_middleware.JWTAuthMiddleware`.

## HTTP API Surface
### Auth
- `POST /api/auth/login/` → email/password login, returns JWT.
- `POST /api/auth/logout/` → session logout.
- `POST /api/auth/guest/` → guest login, returns JWT.

### Rooms
- `POST /api/rooms/create/` → create room (public/private + entry mode). Returns `room_password` once for private/password rooms.
- `POST /api/rooms/join/` → join room (password or approval flow). Returns `status` (`PENDING`/`APPROVED`) and `is_host`.
- `POST /api/rooms/approve/` → host approves a pending participant by `room_id` and `user_id`.

## Real-Time Sync (WebSockets)
- **Endpoint**: `ws/room/<room_code>/`
- **Consumer**: `sync.consumers.RoomPresenceConsumer`
  - Validates: authenticated user, room exists, participant approved.
  - Joins group `room_<code>` and emits presence events (`USER_JOINED`, `USER_LEFT`).
  - Broadcasts room events:
    - `CHAT_MESSAGE` → everyone
    - `PLAY`, `PAUSE`, `SEEK` → host only
  - Chat can be disabled per room (`is_chat_enabled`), returning an `ERROR` payload when disabled.
  - Playback events include `time` payload and are ignored from non-hosts.
  - Chat messages are real-time only and are not persisted to the database (current implementation).


## Data Model
### User
- UUID primary key.
- Email + password (optional for guests).
- `display_name`, `is_guest`, `is_staff`, `is_superuser`.
- `last_seen`, `created_at` timestamps.

### Room
- UUID primary key, unique `code`.
- Host: FK to `User`.
- Privacy: `is_private`, `entry_mode` (`APPROVAL` or `PASSWORD`).
- Optional hashed entry password (auto-generated 8-char password, shown once).
- Media fields: `video_provider`, `video_id`.
- `is_chat_enabled`, `is_active`.

### RoomParticipant
- FK to `Room` and `User`.
- `status`: `PENDING` or `APPROVED`.
- `joined_at`, `last_heartbeat`.
- Unique constraint on (`room`, `user`).

## Request/Message Flow Summary
1. **Login** via HTTP API → JWT returned.
2. **Create/Join room** via HTTP API → participant created/approved (or pending).
3. **Connect to WebSocket** with `?token=` → consumer validates participant.
4. **Broadcast events** (chat or playback) via channel layer to all room members.

## Notes / TODO Candidates
- Add `ALLOWED_HOSTS` and production settings.
- Add migrations/models for `chat`, `providers`, `common` as features expand.
- Consider move to PostgreSQL for production.
- Consider rate limiting and audit logs for room events.
