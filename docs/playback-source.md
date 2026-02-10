# PlaybackSource Architecture

This document defines the PlaybackSource abstraction, which normalizes how external video providers are integrated into the StreamIt backend.

The goal is to support multiple playback providers (Vidking, YouTube, etc.) without leaking provider-specific logic into rooms, Redis, or core lifecycle code.

## 1. PlaybackSource Contract

A PlaybackSource represents what is being played in a room, independent of how it is rendered.

### Canonical PlaybackSource Fields

PlaybackSource
- provider: string
  - Identifier for the playback provider.
  - Example: "vidking"
- media_type: "movie" | "tv"
  - Distinguishes standalone movies from episodic content.
- external_id: string
  - Provider-agnostic external identifier.
  - Example: TMDB ID ("1078605")
- season: number | null
  - Required only when media_type = "tv"
- episode: number | null
  - Required only when media_type = "tv"
- supports_events: boolean
  - Whether the provider emits playback events (play, pause, seek).
- supports_progress: boolean
  - Whether the provider can report playback progress.
- capabilities:
  - seek: boolean
  - pause: boolean
  - resume: boolean
  - autoplay: boolean

### Design Rules

- A PlaybackSource never stores URLs
- A PlaybackSource never stores UI preferences
- A PlaybackSource never talks to Redis or the database
- A PlaybackSource is pure description + capability

## 2. Vidking Adapter Behavior

Vidking is treated as a passive embed provider.

It does not:

- Provide metadata APIs
- Control playback authority
- Communicate directly with the backend

### Provider Identifier

provider = "vidking"

### URL Construction (Derived, Not Stored)

Movie
- /embed/movie/{external_id}

TV Episode
- /embed/tv/{external_id}/{season}/{episode}

### Optional Query Parameters (Frontend-only)

These parameters are never stored in the backend:

- color
- autoPlay
- nextEpisode
- episodeSelector
- progress

They are supplied by the frontend at render time.

### Vidking Capabilities

supports_events = true
supports_progress = true

capabilities:
- seek = true
- pause = true
- resume = true
- autoplay = true

## 3. What Rooms Store vs What Is Derived

### Stored in Room (Database)

Rooms store only the minimal playback identity:

Room
- playback_provider
- playback_external_id
- playback_media_type
- playback_season (nullable)
- playback_episode (nullable)

### Never Stored in Database

The following are explicitly forbidden from persistence:

- Embed URLs
- iframe HTML
- Provider query parameters
- UI preferences
- Watch progress
- Player colors
- Autoplay flags

### Derived at Runtime

Derived values include:

- Embed URL
- Viewer count (from Redis)
- Playback progress (from Redis / runtime state)
- Host connection state

This ensures:

- Database remains provider-agnostic
- Redis remains authoritative for live state
- Frontend remains flexible

## 4. Event Handling Philosophy

### Authority Model (Critical)

Playback authority always belongs to the room host, never the provider.

Vidking emits events via postMessage, but these are informational, not authoritative.

### Correct Event Flow

Vidking iframe
    ↓ postMessage
Frontend
    ↓ WebSocket event (PLAY / PAUSE / SEEK)
RoomPresenceConsumer
    ↓ Redis (authoritative state)
Other clients

### Backend Rules

- Non-host playback commands are silently ignored
- Playback state is stored centrally
- Clients never infer state locally
- Providers never bypass WebSocket authority

### Explicit Non-Behavior

- The backend does not trust iframe events directly
- The backend does not auto-sync playback
- The backend does not persist progress (yet)

## 5. Future Compatibility Guarantees

This abstraction guarantees:

- New providers can be added without schema changes
- Playback logic remains centralized
- Tests remain deterministic
- Redis remains the single source of live truth

Examples of future providers:

- YouTube embeds
- Vimeo
- Self-hosted MP4
- DRM-based players

All must conform to the PlaybackSource contract.

## Status

- PlaybackSource abstraction: STABLE
- Vidking adapter: SUPPORTED
- Metadata providers (TMDB): OUT OF SCOPE
- Progress persistence: OUT OF SCOPE
