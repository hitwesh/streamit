# CHANGELOG

This file records **behavioral and architectural changes**, not raw commits.  
Git history tracks *what* changed; this file tracks *why*, *how*, and *what must never break*.

---

## 2026-02-29 — Status Update (NO CHANGE)

### Notes
- No update today.
- No code was pushed.
- No changelog-worthy behavior changes today.

## 2026-03-01 — Environment Config, Health Check, and Logging Baseline (STABLE)

### Feature
Completed the second production-readiness layer on top of the settings split: environment-driven secrets/config, deploy health probing, and baseline runtime logging.

### Behavior
- Added dotenv loading in `core.settings.base` and switched key runtime settings to environment sources.
- Removed hardcoded values for:
	- `SECRET_KEY`
	- `REDIS_URL`
- Updated channel layer host configuration to use `REDIS_URL` directly.
- Added a backend-local `.env` template/config with required keys:
	- `SECRET_KEY`
	- `DEBUG`
	- `REDIS_URL`
	- `TMDB_API_KEY`
- Added `GET /api/health/` endpoint for uptime checks and deployment probes.
- Added root console logging configuration with default `INFO` level.

### Guarantees
- Existing functional behavior remains unchanged for local development when `.env` is present.
- Redis connectivity is now centrally controlled by one env variable instead of duplicated literals.
- Health checks can be performed by platforms/load balancers without touching business endpoints.

### Operational Notes
- Development `DEBUG` is now environment-controlled via `core.settings.development`.
- `.env` remains ignored by version control to avoid leaking secrets.

### Constraints
- This phase establishes baseline observability/config only; advanced structured logging sinks/formatters are not introduced yet.
- Secret rotation and external secret managers are still pending future production hardening phases.

## 2026-03-01 — Settings Split Foundation (STABLE)

### Feature
Production-readiness configuration split introduced with environment-specific Django settings modules.

### Behavior
- Replaced single-module settings with a package split:
	- `core.settings.base` for shared settings
	- `core.settings.development` for local defaults (`DEBUG=True`, local hosts)
	- `core.settings.production` for deployment defaults (`DEBUG=False`, explicit hosts)
- Updated runtime entry points to default to development settings:
	- `manage.py`
	- `core/asgi.py`
	- `core/wsgi.py`

### Guarantees
- Existing development behavior remains unchanged by default.
- Production-specific overrides now have a dedicated module path (`DJANGO_SETTINGS_MODULE=core.settings.production`).
- Shared app config (auth, channels, Redis, REST, allauth) stays centralized in `base.py` to avoid drift.

### Constraints
- This phase establishes structure only; no container, secret manager, or logging pipeline changes are enforced yet.
- Current production hosts remain placeholder values pending deployment-specific configuration.

## 2026-03-01 — Frontend Contract Freeze Prep (STABLE)

### Feature
Non-breaking contract freeze groundwork for response shapes, error codes, and event registry.

### Behavior
- Added centralized `success(...)`/`error(...)` response helpers for future API normalization.
- Added an error code registry for consistent HTTP and WebSocket error payloads.
- Added a WebSocket event registry to eliminate string literal drift.
- Added `/api/v1/...` and `/ws/v1/...` routes alongside existing endpoints for a safe migration path.

### Guarantees
- No existing endpoints or WebSocket payloads were changed.
- Existing clients remain compatible while v1 routes are introduced.

### Constraints
- This phase is preparatory only; no response shape changes have been enforced yet.

## 2026-03-01 — Centralized PermissionService (STABLE)

### Feature
Centralized authorization rules for hosting, playback control, moderation, and chat.

### Behavior
- Room hosting checks are centralized via `PermissionService.can_host`.
- WebSocket role assignment derives host/participant from DB-backed permissions.
- Moderation and playback controls return explicit permission errors when denied.
- Chat now blocks unauthorized users with a structured `CHAT_FORBIDDEN` error.

### Guarantees
- Host authority is evaluated consistently across HTTP and WebSocket paths.
- Permission checks are auditable and testable from a single location.
- No changes to playback state transitions or room lifecycle rules.

### Constraints
- Permission checks remain synchronous and do not touch ORM in async contexts.
- Username-less users remain blocked from hosting and WebSocket joins.

### Tests
- Added PermissionService unit tests for host control and guest hosting denial.

## 2026-02-28 — Identity & Username Enforcement (STABLE)

### Feature
Identity hardening for Google and guest flows with explicit username selection and host gating.

### Behavior
- Google-created accounts no longer receive auto-generated usernames; they start with `username=None`.
- Username-less users are blocked from hosting rooms and from joining rooms via WebSocket.
- Guests and anonymous users cannot host rooms.
- `POST /api/set-username/` lets authenticated users claim a username and syncs `display_name`.
- Guest login is DB-backed and returns JWT access tokens for consistent session handling.

### Guarantees
- Hosting is allowed only for authenticated, non-guest users with a valid username.
- WebSocket identity is derived from DB state, not client payloads.
- Username uniqueness is enforced case-insensitively at the API level.

### Constraints
- No playback or room lifecycle logic changes.
- Username format is limited to 3-20 characters, alphanumeric or underscore.
- Allauth uses a custom account adapter to prevent silent username assignment.

### Tests
- Username completion flow tested with success and duplicate rejection cases.

## 2026-02-26 — Provider Search Layer (STABLE)

### Feature
Normalized provider search backed by TMDB with Redis caching.

### Behavior
- `GET /api/rooms/search/?q=<query>&page=<n>` returns normalized search results.
- Search results use a provider-agnostic contract (`ContentSearchResult`).
- Results are cached in Redis for 1 hour to reduce TMDB calls.

### Guarantees
- Search does not touch playback state or room lifecycle.
- Provider selection remains isolated inside `providers/`.

### Constraints
- Requires `TMDB_API_KEY` to be set in the environment.
- No provider-specific response formats leak to clients.

### Tests
- Provider search is validated with a mocked TMDB response.

## 2026-02-26 — Industrial Chat Rate Limiting (STABLE)

### Feature
Sliding-window chat rate limiting with enforced cooldown.

### Behavior
- Limit: 5 messages per 3 seconds per user per room.
- Exceeding the window triggers a 10-second cooldown.
- During cooldown, messages are rejected immediately.

### Guarantees
- Room-scoped, user-scoped enforcement.
- Redis-only enforcement with no DB writes.

### Constraints
- No async ORM access added to the chat path.
- No channel layer internals used.

### Tests
- Chat rate limit test now avoids duplicate suppression and consumes broadcasts before asserting cooldown errors.

## 2026-02-26 — Provider Registry (STABLE)

### Feature
Provider registry that maps provider names to existing builder and embed URL functions.

### Behavior
- Provider selection can be centralized via `get_provider` without changing current resolver usage.
- Unknown providers raise a `ValueError`.

### Guarantees
- No changes to existing provider contract or resolver behavior.
- No new provider-specific logic introduced outside `providers/`.

### Tests
- Provider registry tests added for Vidking resolution and unknown provider handling.

## 2026-02-16 — Room Moderation (STABLE)

### Feature
Host moderation actions: mute, kick, and ban with Redis-backed state.

### Behavior
- Muted users cannot send chat messages.
- Banned users are disconnected and blocked from reconnecting.
- Kicked users are disconnected once but may reconnect.

### Guarantees
- Moderation is host-authoritative and room-scoped.
- Enforcement is Redis-backed with no DB writes.

### Constraints
- No async ORM access added to moderation checks.
- No channel layer internals used.

## 2026-02-16 — Chat Hardening (STABLE)

### Feature
Chat hardening with length limits, duplicate suppression, and history caps.

### Behavior
- Messages longer than 500 characters are rejected with an `ERROR` event.
- Duplicate messages from the same user within a short window are blocked.
- Per-room chat history is capped at the most recent 500 messages.

### Guarantees
- No disconnects are triggered by chat violations.
- Enforcement is deterministic and Redis-backed.

### Constraints
- No async ORM access added to the chat path.
- No channel layer internals used.

## 2026-02-15 — Redis Chat Rate Limiting (STABLE)

### Feature
Chat messages are rate limited per user per room using Redis.

### Behavior
- Limit: 5 messages per 3 seconds per user per room.
- Excess messages return a structured `ERROR` event.
- No disconnections or side effects beyond the error response.

### Guarantees
- Rate limiting is enforced atomically via Redis INCR with TTL.
- No async ORM access added to the chat path.

### Constraints
- No changes to WebSocket transport or channel layer internals.
- No DB writes for rate limiting.

## 2026-02-15 — Drift Correction Sync Checks (STABLE)

### Feature
Server-side drift correction via SYNC_CHECK and SYNC_CORRECTION events.

### Behavior
- Clients can send `SYNC_CHECK` with their local playback time.
- Server compares against authoritative playback state.
- If drift exceeds threshold, server responds with `SYNC_CORRECTION`.

### Guarantees
- Playback remains host-authoritative.
- Clients can self-correct without polling or manual refresh.

### Constraints
- No new endpoints introduced.
- No Redis behavior changes.
- Async ORM access remains sync-wrapped.

## 2026-02-14 — Versioned Playback State (STABLE)

### Feature
Playback state now includes a monotonically increasing version and broadcasts full snapshots.

### Behavior
- Each host playback action increments the playback state version.
- Playback broadcasts send `PLAYBACK_STATE` snapshots only (no direct PLAY/PAUSE/SEEK events).
- Join snapshots include the current version.

### Guarantees
- Clients can ignore stale state updates using version ordering.
- Playback state remains host-authoritative.

### Constraints
- No new endpoints introduced.
- No Redis behavior changes.
- Async ORM access remains sync-wrapped.

## 2026-02-14 — Resume Progress API (STABLE)

### Feature
Resume endpoint for user watch progress by room code.

### Behavior
- `GET /api/rooms/<room_code>/resume/` returns progress percent, last position seconds, and completion flag.
- When no progress exists, returns zeros and `completed=false`.

### Guarantees
- Read-only endpoint with no side effects.
- Uses existing watch progress records; no schema changes.

### Constraints
- Progress is scoped to the authenticated user and room.
- No Redis access required.

## 2026-02-14 — Playback Completion Finalization (STABLE)

### Feature
Playback completion now finalizes watch progress when the player emits an ended event.

### Behavior
- Host-only PLAYER_EVENT handling updates watch progress.
- Ended events set progress to 100% and mark completion.
- Timeupdate/seeked/pause events update progress without completion.

### Guarantees
- Completion is deterministic and host-authoritative.
- Completed sessions resume from the beginning.
- No change to playback authority or room lifecycle rules.

### Constraints
- No new endpoints introduced.
- No Redis behavior changes.
- Async ORM access remains sync-wrapped.

## 2026-02-14 — Host Playback Progress Sync (STABLE)

### Feature
Host playback commands now persist watch progress on PLAY, PAUSE, and SEEK.

### Behavior
- When the host sends PLAY, PAUSE, or SEEK, the room playback state updates.
- The host's watch progress is synced to the current playback time.

### Guarantees
- Progress updates are host-authoritative.
- Playback state and watch progress cannot drift.
- No client-side dependency is required for host progress persistence.

### Constraints
- No change to playback authority rules.
- No change to WebSocket message types.
- No async ORM access outside sync-wrapped helpers.

## 2026-02-12 — Status Update (NO CHANGE)

### Notes
- No update was made to GitHub.
- No code was pushed.
- No changelog-worthy behavior changes today.

## 2026-02-13 — Status Update (NO CHANGE)

### Notes
- No update was made to GitHub.
- No code was pushed.
- No changelog-worthy behavior changes today.

## 2026-02-11 — Phase 2 Media Provider Integration & Watch Progress (STABLE)

### Feature
Integrated external video provider embedding (Vidking-style) and persistent watch progress tracking.

### Added
- Public embed URL builder for movie and TV content.
- Support for:
	- `color`
	- `autoPlay`
	- `nextEpisode`
	- `episodeSelector`
	- `progress`
- Structured embed URL generation at the backend level.
- Watch progress persistence model.
- Progress update API endpoint.
- Progress retrieval API endpoint.

### Guarantees
- Embed URLs are generated server-side and remain canonical.
- Watch progress is stored per:
	- user
	- room
	- content ID
- Progress is idempotent and updates safely.
- No playback authority rules were changed.
- No existing lifecycle behavior was modified.

### Constraints
- Provider integration does not control playback logic.
- Playback state authority remains host-only.
- Progress persistence does not alter WebSocket behavior.
- No async ORM access was introduced.

### Test Coverage
- Embed URL builder validated.
- Watch progress create/update flows tested.
- Progress retrieval tested.
- Public rooms unaffected.
- Grace lifecycle unaffected.

## ⚠️ Maintenance Rule (Effective 2026-02-01)

From **2026-02-01 onward**, this CHANGELOG is **strictly maintained**.

### Rules
- Every new feature, fix, or behavioral change **must** be recorded here.
- Entries describe **intent, guarantees, and constraints**, not implementation details.
- Temporary hacks, experiments, or reverted work **do not belong here**.
- If a bug is fixed by introducing new behavior, that behavior **must be documented**.
- No backfilling or rewriting past entries except for clarity.

### Maintenance Rule
⬆️ newest entry (today)
⬇️ older entries
⬇️ oldest entries

This file is treated as a **contract** for backend behavior.

---

## 2026-02-10 — Phase 2 Provider Abstraction (STABLE)

### Feature
Provider abstraction layer introduced.

### Behavior
- Rooms can now resolve provider embed URLs through a centralized provider resolver.
- Vidking provider implemented as first supported video backend.
- Provider URL generation supports:
  - Movie
  - TV (season/episode)
  - Optional playback start time

### Guarantees
- Room model does not construct embed URLs directly.
- Provider logic is isolated inside the providers app.
- Switching providers does not require room model changes.
- Existing room lifecycle, Redis state, and playback sync behavior remain unchanged.

### Constraints
- Providers must expose a deterministic embed URL.
- No provider-specific logic is allowed inside WebSocket consumers.
- Provider resolution must remain synchronous and pure.

### Stability
All existing lifecycle, Redis, and WebSocket authority tests remain green.

## 2026-02-10 — Phase 2 Public Room Discovery (STABLE)

### Feature
- Public rooms listing endpoint (`GET /api/rooms/public/`)

### Behavior
- Only non-private rooms are listed
- Rooms must be LIVE to appear
- Viewer count is derived from Redis presence
- Redis is the realtime source; DB is authoritative fallback

### Guarantees
- Private rooms never appear
- Expired or deleted rooms never appear
- Redis failure does not corrupt DB state

### Constraints
- Viewer counts are approximate and realtime
- No side effects on read

## 2026-02-08 — Phase 1 Complete (STABLE)

### Summary
Phase 1 complete: room lifecycle, grace handling, Redis integration, and tests.

### Guarantees
- Room lifecycle transitions are enforced and terminal states are absolute.
- Grace handling is deterministic and does not depend on WebSocket timing.
- Redis presence and grace keys remain authoritative for realtime state.
- Tests lock in lifecycle and realtime behavior.

## 2026-02-08 — Phase 2 Public Room Discovery (STABLE)

### Summary
Added a read-only public rooms API backed by Redis viewer counts with strict filtering for active, non-private rooms.

### Added
- Redis helper `get_viewer_count` for participant set cardinality.
- `get_public_rooms` service to filter live/grace public rooms only.
- GET /api/rooms/public/ endpoint to return code, host, viewer count, and created timestamp.
- Tests covering public listing and private room exclusion.

### Guarantees
- Private rooms are never exposed.
- Expired or deleted rooms are never listed.
- No WebSocket or state mutation dependencies.

## 2026-02-08 — Room Lifecycle Guardrails (STABLE)

### Summary
Centralized room state transition rules in the model and blocked expiration logic from touching deleted rooms.

### Changed
- Room lifecycle transitions now flow through a single guard; terminal states are absolute.
- Expiration management command only targets active GRACE rooms and skips deleted rooms.
- WebSocket tests now wait for specific bootstrap events instead of assuming ordering.
- Grace-with-participants test marks room LIVE and runs `expire_rooms` after grace to match current lifecycle behavior.
- Async ORM access in websocket tests is wrapped with `database_sync_to_async`.

### Guarantees
- EXPIRED cannot transition back to LIVE.
- DELETED is terminal and cannot be overwritten by expiry.

## 2026-02-07 — Status Update (NO CHANGE)

### Notes
- No update was made to GitHub.
- No code was pushed.
- No changelog-worthy behavior changes today.

## 2026-02-06 — Lifecycle Enforcement & Test Suite (STABLE)

### Summary
Added deterministic room expiry via a management command, hardened Redis async usage, and formalized the test suite layout.

### Added
- Management command `expire_rooms` to mark GRACE rooms EXPIRED and clean related Redis keys.
- Test coverage for room lifecycle, join behavior, chat persistence, playback state creation, and Redis grace TTL.

### Changed
- Redis async client is no longer cached to prevent cross-event-loop reuse.
- Tests use per-class event loops for Redis async helpers.
- Legacy app-level `tests.py` files removed in favor of package-based `tests/` directories.

### Guarantees
- Room expiry is deterministic without polling or WebSocket triggers.
- Redis cleanup remains best-effort and does not affect DB authority.
- Django test discovery is unambiguous across apps.

## 2026-02-06 — Phase 1.1-1.3 Room Lifecycle (STABLE)

### Summary
Formalized room lifecycle state in the DB and shifted grace timing authority to Redis TTL.

### Added (Phase 1.1)
- `Room.state` with enum values: CREATED, LIVE, GRACE, EXPIRED, DELETED.

### Added (Phase 1.2)
- Explicit DB-only state transition helpers: `mark_live`, `mark_grace`, `mark_expired`, `mark_deleted`.
- Invalid transitions are ignored by design.

### Added (Phase 1.3)
- Redis TTL grace key `room:{code}:grace` with centralized helpers.
- Host disconnect starts grace in Redis and marks DB state GRACE.
- Host reconnect clears Redis grace and marks DB state LIVE.
- Lazy expiry: first join after TTL expiry marks DB state EXPIRED and closes.

### Guarantees
- Redis is authoritative for grace timing; DB records durable state only.
- No polling or background jobs for expiry.
- No async ORM access inside consumers (DB changes remain sync-wrapped).

### Constraints
- `host_disconnected_at` remains for audit only; timing no longer depends on it.
- Legacy `is_in_grace` and `grace_expired` remain until later cleanup.

## 2026-02-05 — Status Update (NO CHANGE)

### Notes
- No update was made to GitHub.
- No code was pushed.
- Next phase is coded and awaiting testing.

## 2026-02-04 — Phase 0 Realtime Stabilization (STABLE)

### Summary
Stabilized the realtime backend foundation without changing behavior.

### Guarantees
- Async WebSocket consumers do not access Django ORM objects directly.
- All ORM access is isolated behind `database_sync_to_async` helpers.
- Redis write semantics are centralized in a dedicated layer.
- Redis keys for room state, host status, and participants are canonical and stable.
- Reconnect behavior, playback authority, chat behavior, and presence semantics are unchanged.

### Constraints
- Consumers must express intent only and must not:
	- access Redis clients directly
	- construct Redis payloads
	- access ORM objects
- Any violation of these rules is a regression.

### Notes
This phase introduces no new features and exists solely to remove hidden technical debt
before advancing to room lifecycle state machines.

## 2026-02-04 — USER_JOINED Exclusion on Connect (STABLE)

### Fix
- USER_JOINED now excludes the connecting socket during WebSocket connect.

### Guarantees
- The joining client does not receive its own USER_JOINED event.
- All other connected participants still receive USER_JOINED.

## 2026-02-04 — Redis Live Presence & Cache Registry (STABLE)

### Feature
- Central Redis live-room registry and cache helpers are now the source for live room visibility.
- Room state, host status, and participant sets are cached on connect/disconnect and participant broadcasts.
- Default Redis connection is exposed via `REDIS_URL`.


## 2026-02-03 — Redis Room Cache Keys (STABLE)

### Feature
Canonical Redis cache keys for room state, host status, and participant sets.

### Guarantees
- Room cache entries live in Redis, not the database.
- Key format is stable across the backend for room state, host status, and participants.
- Default Redis connection uses `REDIS_URL` when not explicitly configured.

## 2026-02-03 — Public Room Discovery API (STABLE)

### Feature
Public rooms can be listed for homepage discovery.

### Endpoint
GET /api/rooms/public/

### Rules
- Only non-private rooms are listed.
- Deleted rooms never appear.
- Viewer count is derived from live presence (not stored).
- No authentication required.

### Guarantees
- Private rooms are never exposed.
- Listing is read-only and side-effect free.

## 2026-02-02 — Host Room Deletion Auth Fix (STABLE)

### Fix
- Room deletion endpoint now uses session-based authentication.
- Aligns delete behavior with create/join APIs.

### Guarantees
- Only the room host can delete a room.
- JWT tokens are not accepted for HTTP deletion.
- Deletion works with the same session used for login.

## 2026-02-02 — Host Grace Period & Room Persistence (STABLE)

### Feature
Host disconnect grace handling for rooms.

### Behavior
- When the host disconnects, the room enters a grace period (10 minutes).
- Playback freezes; participants remain connected.
- Host may reconnect using the same room code to resume the session.
- If grace expires, the room is permanently closed.

### Guarantees
- Rooms are never destroyed due to transient network failures.
- Reconnecting within grace restores playback and presence.
- No in-memory room state; database is authoritative.

### Constraints
- No async ORM access in consumers.
- Grace timing is server-enforced.

### Added
- Host can permanently delete a room via explicit API call.
- Room deletion immediately disconnects all participants.
- During host grace period, chat remains enabled for participants.

### Guarantees
- Room deletion is explicit and irreversible.
- Grace period does not restrict chat.
- Playback control remains host-only.

## 2026-02-01 — Room State Synchronization (STABLE)

### Documentation (PROCESS)
**Manual end-to-end testing reference added**
- Added a gold-reference manual testing guide at `docs/manual-testing.md`.
- Captures the required E2E flow using PowerShell (HTTP) and `wscat` (WebSockets), including expected outputs.
- Explicitly documents first-run DB initialization ordering (`makemigrations` → `migrate`) and the typical fresh-clone shortcut (`migrate` only) since migrations are committed.
- Documents superuser creation as the default “host/admin” account for manual testing.

### Feature
**Room playback state sync on join**
- New participants receive the current playback state immediately on WebSocket connect.
- State includes:
	- `is_playing`
	- `time`

### Why
Without this, late joiners start desynced from the host, breaking the core watch-together experience.

### Guarantees
- Every successful WebSocket join emits **exactly one** `PLAYBACK_STATE` message.
- Playback state is **authoritative from the host only**.
- Late joiners never infer or calculate state locally.

### Async Safety Rule
- No ORM access is allowed directly inside async WebSocket handlers.
- All database access must go through `database_sync_to_async`.
- Consumers must receive fully-resolved data (no lazy relations).

### Do NOT duplicate
- Do not recalculate playback state in consumers.
- Do not infer playback state from recent events.
- Always read from the centralized playback state helper.

### ✅ WebSocket Authority & Playback Enforcement (STABLE)

### Feature
- Host-only playback enforcement confirmed
- Only the room host can emit `PLAY`, `PAUSE`, and `SEEK` events.
- Playback events from non-hosts are silently ignored.

### Why
This prevents desynchronization, abuse, and authority confusion in watch-together sessions.

### Guarantees
- Playback state is controlled by exactly one user (the host).
- Non-host playback commands:
	- Do not broadcast
	- Do not error
	- Do not disconnect the client
- All connected clients remain in sync with the host.

### Explicit Non-Behavior
- The server does not acknowledge or reject invalid playback attempts.
- The client must not rely on server errors to detect permissions

---

## 2026-01-31 — Chat Controls & Realtime Core (STABLE)

### Feature
**Chat enable / disable per room**
- Rooms can toggle chat via `Room.is_chat_enabled`.
- When disabled, chat messages are rejected with:
	```json
	{ "type": "ERROR", "message": "Chat is disabled in this room" }
	```

**Realtime presence and playback sync foundation**

WebSocket room presence broadcasts:
- `USER_JOINED`
- `USER_LEFT`

Host-only playback events:
- `PLAY`
- `PAUSE`
- `SEEK`

### Guarantees
- Only the room host can emit playback control events.
- Presence events are emitted only on WebSocket connect/disconnect.
- Chat messages are persisted only when chat is enabled.

### Rejection Behavior
- Invalid or unauthorized WebSocket events are silently ignored.
- The server does not disconnect clients for protocol violations.
- Errors are returned only for user-relevant actions (e.g. chat disabled).

---

## 2026-01-30 — Initial Realtime Foundation (STABLE)

### Feature
- WebSocket routing via Django Channels.
- Redis channel layer for fan-out messaging.
- JWT-based authentication for WebSocket connections.

### Guarantees
- All WebSocket connections require authenticated users.
- JWT must be supplied explicitly (`?token=`); sessions alone are insufficient.

---

## 2026-01-29 — Core Rooms & Authentication (STABLE)

### Feature
- Room and participant data models.
- Room creation API.
- Room join API with idempotent behavior.
- Custom email-based authentication backend.

### Guarantees
- Room codes are globally unique.
- Joining an already-joined room is safe and returns success.
- Hosts are automatically approved participants.

---

## 2026-01-28 — Project Initialization

### Feature
- Django project scaffold created.
- Core apps registered.

---

## 2026-01-16 — Repository Bootstrap

### Feature
- Initial repository structure.
- Removal of temporary test artifacts.


---


