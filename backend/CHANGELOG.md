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

## 2026-02-01 — Room State Synchronization (STABLE)

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


