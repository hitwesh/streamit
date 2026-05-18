import type { SessionUser } from "@/lib/api"

const SESSION_KEY = "streamit.session"
const ROOM_KEY_PREFIX = "streamit.room."
const LAST_ROOM_KEY = "streamit.room.last"

export type StoredSession = {
  token: string
  user: SessionUser
}

export type RoomMeta = {
  room_id: string
  code: string
  status: "PENDING" | "APPROVED"
  is_host: boolean
  entry_mode?: string | null
  is_private?: boolean
  room_password?: string
}

export function loadSession(): StoredSession | null {
  if (typeof window === "undefined") return null

  const raw = localStorage.getItem(SESSION_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as StoredSession
  } catch {
    return null
  }
}

export function saveSession(session: StoredSession): void {
  if (typeof window === "undefined") return
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function clearSession(): void {
  if (typeof window === "undefined") return
  localStorage.removeItem(SESSION_KEY)
}

export function saveRoomMeta(meta: RoomMeta): void {
  if (typeof window === "undefined") return

  localStorage.setItem(`${ROOM_KEY_PREFIX}${meta.code}`, JSON.stringify(meta))
  localStorage.setItem(LAST_ROOM_KEY, meta.code)
}

export function loadRoomMeta(roomCode: string): RoomMeta | null {
  if (typeof window === "undefined") return null

  const raw = localStorage.getItem(`${ROOM_KEY_PREFIX}${roomCode}`)
  if (!raw) return null

  try {
    return JSON.parse(raw) as RoomMeta
  } catch {
    return null
  }
}

export function clearRoomMeta(roomCode: string): void {
  if (typeof window === "undefined") return
  localStorage.removeItem(`${ROOM_KEY_PREFIX}${roomCode}`)
}

export function loadLastRoomCode(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(LAST_ROOM_KEY)
}
