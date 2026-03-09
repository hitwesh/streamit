// Central WebSocket manager — one shared socket for the entire room session.
// All components read/write through this module; none open their own sockets.

// ─── Event types (must match backend sync/events.py WSEvents) ────────────────

export type ClientEvent =
  // Chat
  | { type: "CHAT_MESSAGE"; message: string }
  // Playback — host only. Use PLAY/PAUSE/SEEK (not PLAYER_EVENT) for sync.
  | { type: "PLAY"; time: number }
  | { type: "PAUSE"; time: number }
  | { type: "SEEK"; time: number }
  // Watch-progress tracking (backend updates WatchProgress model, does NOT broadcast)
  | { type: "PLAYER_EVENT"; data: PlayerEventData }
  // Sync check — ask server if local time has drifted
  | { type: "SYNC_CHECK"; client_time: number }
  // Moderation — host only
  | { type: "MUTE_USER"; user_id: string }
  | { type: "BAN_USER"; user_id: string }
  | { type: "KICK_USER"; user_id: string }

export type PlayerEventData =
  | { event: "ended"; currentTime: number; duration: number; progress: number }
  | { event: "timeupdate" | "seeked" | "pause"; currentTime: number; duration: number; progress: number }
  | { event: "quality_change"; quality: string }
  | { event: "subtitle_change"; subtitle: string }

export type ServerEvent =
  | { type: "CHAT_HISTORY"; messages: ChatMessage[] }
  | { type: "CHAT_MESSAGE"; user: string; message: string }
  | { type: "PLAYBACK_STATE"; is_playing: boolean; time: number; version: number }
  | { type: "ROOM_PARTICIPANTS"; participants: string[]; host: string }
  | { type: "USER_JOINED"; user: string }
  | { type: "USER_LEFT"; user: string }
  | { type: "HOST_DISCONNECTED"; grace_seconds: number }
  | { type: "HOST_RECONNECTED" }
  | { type: "ROOM_DELETED" }
  | { type: "SYNC_CORRECTION"; time: number; version: number }
  | { type: "ERROR"; message: string; code?: string }

export interface ChatMessage {
  user: string
  message: string
  created_at: string
}

// ─── Module state ─────────────────────────────────────────────────────────────

let socket: WebSocket | null = null
let currentRoomCode: string | null = null
let currentToken: string | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

type MessageHandler = (event: ServerEvent) => void
const handlers = new Set<MessageHandler>()

// Backend-defined policy/auth close codes from sync/consumers.py.
const NON_RETRY_CLOSE_CODES = new Set([
  4001, // not authenticated
  4002, // room does not exist
  4003, // forbidden / not approved participant
  4004, // room grace expired
  4005, // room inactive
  4010, // banned user
  4011, // force disconnect (kick/ban)
])

// ─── Internal socket factory ──────────────────────────────────────────────────

function createSocket(roomCode: string, token: string): WebSocket {
  let openedAtLeastOnce = false

  const ws = new WebSocket(
    `ws://localhost:8000/ws/room/${roomCode}/?token=${token}`
  )

  ws.onopen = () => {
    openedAtLeastOnce = true
    console.log("[WS] connected")
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  ws.onmessage = (event) => {
    try {
      const data: ServerEvent = JSON.parse(event.data)
      handlers.forEach((handler) => handler(data))
    } catch {
      console.error("[WS] failed to parse message", event.data)
    }
  }

  ws.onerror = () => {
    // Browsers intentionally provide very little detail on WebSocket errors.
    // Use warn-level logging to avoid noisy Next.js error overlays for expected
    // transient transport failures (server restart, network flap, auth reject).
    console.warn("[WS] transport error", {
      url: ws.url,
      readyState: ws.readyState,
    })
  }

  ws.onclose = (event) => {
    const closeCode = event.code
    const retryable = !NON_RETRY_CLOSE_CODES.has(closeCode)

    console.warn("[WS] closed", {
      code: closeCode,
      reason: event.reason || "(empty)",
      wasClean: event.wasClean,
      retryable,
    })

    socket = null

    // If the socket never opened, this was likely a handshake/auth/policy reject.
    // Do not loop reconnect attempts in that state.
    if (!openedAtLeastOnce) {
      console.warn("[WS] reconnect skipped: initial handshake was not accepted")
      return
    }

    if (!retryable) {
      console.warn("[WS] reconnect skipped due to non-retryable close code")
      return
    }

    // Re-attach handlers by re-using the same createSocket call so onmessage
    // and all other handlers are wired correctly on the new socket.
    reconnectTimer = setTimeout(() => {
      if (currentRoomCode && currentToken) {
        socket = createSocket(currentRoomCode, currentToken)
      }
    }, 2000)
  }

  return ws
}

// ─── Public API ───────────────────────────────────────────────────────────────

/** Open the room socket if it isn't already open. Safe to call multiple times. */
export function connectToRoom(roomCode: string, token: string): void {
  if (socket) return

  if (!roomCode) {
    console.warn("[WS] connect skipped: missing room code")
    return
  }

  if (!token) {
    console.warn("[WS] connect skipped: missing token")
    return
  }

  currentRoomCode = roomCode
  currentToken = token
  socket = createSocket(roomCode, token)
}

/** Send any client event. Silently drops if the socket is not open. */
export function sendMessage(message: ClientEvent): void {
  if (!socket || socket.readyState !== WebSocket.OPEN) return
  socket.send(JSON.stringify(message))
}

/**
 * Register a handler for all incoming server events.
 * Returns an unsubscribe function — call it on component unmount to
 * prevent memory leaks and stale-closure bugs.
 *
 * @example
 * useEffect(() => {
 *   return addMessageHandler((event) => { ... })
 * }, [])
 */
export function addMessageHandler(handler: MessageHandler): () => void {
  handlers.add(handler)
  return () => handlers.delete(handler)
}

/** Close the socket and stop any pending reconnect. */
export function disconnectSocket(): void {
  if (reconnectTimer !== null) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  if (socket) {
    // Remove onclose before calling close() so the reconnect logic doesn't fire
    // when we intentionally disconnect (e.g. user leaves the room).
    socket.onclose = null
    socket.close()
    socket = null
  }

  currentRoomCode = null
  currentToken = null
}
