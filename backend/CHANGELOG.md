# CHANGELOG

This file records **behavioral and architectural changes**, not raw commits.  
Git history tracks *what* changed; this file tracks *why*, *how*, and *what must never break*.

---

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


