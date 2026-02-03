# StreamIt — Industrial-Grade Master Roadmap

This document defines **what must exist**, **in what order**, and **why** to turn StreamIt into a production-ready, scalable streaming platform.

This roadmap assumes:
- **Django + Channels + Redis** backend
- **External streaming APIs** (VidKing or similar)
- **Web frontend** (later)
- **Long-term maintainability** as a first-class goal

## Core Principles (Do Not Break These)
- Backend is the source of truth
- Host authority is absolute
- Redis = realtime state, DB = durability
- Async code never touches ORM directly
- Every feature must survive reconnects
- No feature ships without a test path
- CHANGELOG is mandatory

If a decision violates one of these, it is wrong.

---

## Phase 0 — Foundation Freeze (Mandatory)
**Goal:** Stabilize what already exists and remove hidden technical debt.

### Tasks
- Remove all usage of `channel_layer._redis`
- Introduce dedicated Redis client layer
- Centralize Redis keys:
  - `room:{code}:state`
  - `room:{code}:participants`
  - `room:{code}:host_status`
- Ensure all ORM access is wrapped with `database_sync_to_async`
- Audit consumers for:
  - Lazy FK access
  - Implicit DB hits
- Verify migrations are complete

### Deliverables
- Stable WebSocket connections
- Zero runtime Redis/Channels internals usage
- CHANGELOG entry

---

## Phase 1 — Room Lifecycle & State Machine
**Goal:** Rooms behave predictably from birth to destruction.

### Room States
`CREATED → LIVE → GRACE → EXPIRED → DELETED`

### Tasks
- Explicit room state field
- Grace timer stored in Redis (TTL)
- Host disconnect triggers GRACE
- Host reconnect restores LIVE
- Grace expiry triggers EXPIRED
- Manual delete API (host only)

### Guarantees
- No ghost rooms
- No infinite Redis keys
- No DB bloat

---

## Phase 2 — Public Rooms & Discovery
**Goal:** Twitch-like public visibility without chaos.

### Tasks
- `Room.is_public`
- `Room.viewer_count` (Redis → DB sync)
- API: `GET /api/rooms/public/`
- Pagination + sorting
- Exclude:
  - Private rooms
  - Expired rooms

### Guarantees
- Public list is fast
- Redis crash does not break DB
- Read-only endpoint

---

## Phase 3 — Stream Provider Abstraction
**Goal:** Decouple StreamIt from any single video source.

### Create Abstraction
**PlaybackSource**
- provider
- stream_id
- qualities
- subtitles
- duration
- poster

### Tasks
- VidKing adapter (read-only first) https://www.vidking.net/#documentation
- Normalize API response
- Store metadata only
- Validate stream availability on host select

### Guarantees
- No video bytes stored
- Providers are swappable
- Backend stays platform-agnostic

---

## Phase 4 — Playback Engine (Critical)
**Goal:** Perfect sync for all users.

### Playback Events
- PLAY
- PAUSE
- SEEK
- CHANGE_QUALITY
- CHANGE_SUBTITLE

### Tasks
- Versioned playback state
- Host-only enforcement
- Redis playback authority
- Drift prevention logic
- Late joiner resync

### Guarantees
- Late joiners always sync
- Non-host commands ignored
- No playback inference

---

## Phase 5 — Chat System Hardening
**Goal:** Chat scales without hurting playback.

### Tasks
- Rate limiting (Redis)
- Message batching
- Chat enable/disable (already present)
- Host moderation hooks
- Persistence limits

### Guarantees
- Chat never blocks playback
- Chat works during host absence
- Abuse cannot crash room

---

## Phase 6 — Search & Content Catalog
**Goal:** Netflix-style browsing experience.

### Tasks
- Movie/Show search API
- Redis caching
- Poster + metadata normalization
- Pagination + filters
- API rate-limit protection

### Guarantees
- Fast responses
- API provider respected
- Search reusable across UI

---

## Phase 7 — Auth & Access Control
**Goal:** Clear, predictable permissions.

### Tasks
- Guest vs Auth user separation
- Token scopes
- Host privilege validation everywhere
- Optional role system (future)

### Guarantees
- No privilege escalation
- Clear error responses
- WebSocket auth consistency

---

## Phase 8 — Testing Framework (Mandatory)
**Goal:** Confidence before scale.

### Required Tests
- PowerShell HTTP tests
- JS WebSocket test harness
- Reconnect chaos tests
- Redis restart simulation
- Host crash scenarios

### Guarantees
- Known failure modes
- Predictable recovery
- No silent corruption

---

## Phase 9 — Frontend Contract Freeze
**Goal:** Frontend can be built independently.

### Tasks
- OpenAPI spec
- WebSocket event contract
- Error code registry
- Versioned API paths

### Guarantees
- No breaking changes
- Clear integration points
- Stable client behavior

---

## Phase 10 — Production Readiness
**Goal:** Deploy without fear.

### Tasks
- Dockerization
- Environment-based config
- Secrets management
- Structured logging
- Monitoring hooks

---

## Phase 11 — Scale & Optimization (Optional)
### Tasks
- Horizontal scaling
- Sharded Redis (if needed)
- CDN integration
- Analytics pipeline
