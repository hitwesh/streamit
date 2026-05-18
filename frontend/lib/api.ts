const DEFAULT_API_BASE_URL = "http://localhost:8000"

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "")
}

export const API_BASE_URL = normalizeBaseUrl(
  process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL
)

export const WS_BASE_URL = normalizeBaseUrl(
  process.env.NEXT_PUBLIC_WS_BASE_URL ?? API_BASE_URL.replace(/^http/, "ws")
)

export type SessionUser = {
  id: string
  display_name: string
  is_guest: boolean
}

export type LoginResponse = SessionUser & {
  access_token: string
}

export type RoomCreateResponse = {
  room_id: string
  code: string
  is_private: boolean
  entry_mode: string | null
  room_password?: string
}

export type RoomJoinResponse = {
  room_id: string
  code: string
  status: "PENDING" | "APPROVED"
  is_host: boolean
}

export type PublicRoom = {
  code: string
  host: string
  viewers: number
  created_at: string
}

export type SearchResult = {
  provider: string
  stream_id: string
  media_type: string
  title: string
  poster: string | null
  release_year: number | null
}

export type RoomDetail = {
  room_id: string
  code: string
  state: string
  is_active: boolean
  is_private: boolean
  entry_mode: string | null
  is_chat_enabled: boolean
  host: string
  host_id: string
  video_provider: string
  video_id: string
  created_at: string
  is_host: boolean
}

export type ParticipantRecord = {
  id: string
  display_name: string
  status: "PENDING" | "APPROVED"
  is_host: boolean
  is_guest: boolean
}

type RequestOptions = {
  method?: "GET" | "POST"
  body?: unknown
  token?: string | null
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    credentials: "include",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  const contentType = response.headers.get("content-type") ?? ""
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message =
      typeof data === "string"
        ? data
        : data?.error || data?.message || "Request failed"
    throw new Error(message)
  }

  return data as T
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return request("/api/auth/login/", {
    method: "POST",
    body: { email, password },
  })
}

export function guestLogin(displayName: string): Promise<LoginResponse> {
  return request("/api/auth/guest/", {
    method: "POST",
    body: { display_name: displayName },
  })
}

export function logout(): Promise<{ success: boolean }> {
  return request("/api/auth/logout/", {
    method: "POST",
  })
}

export function createRoom(
  payload: {
    is_private: boolean
    entry_mode: string | null
  },
  token?: string | null
): Promise<RoomCreateResponse> {
  return request("/api/rooms/create/", {
    method: "POST",
    body: payload,
    token,
  })
}

export function joinRoom(
  payload: {
    code: string
    password?: string
  },
  token?: string | null
): Promise<RoomJoinResponse> {
  return request("/api/rooms/join/", {
    method: "POST",
    body: payload,
    token,
  })
}

export function approveParticipant(
  payload: {
    room_id: string
    user_id: string
  },
  token?: string | null
): Promise<{ approved: boolean }> {
  return request("/api/rooms/approve/", {
    method: "POST",
    body: payload,
    token,
  })
}

export function deleteRoom(
  payload: { room_id: string },
  token?: string | null
): Promise<{ status: string }> {
  return request("/api/rooms/delete/", {
    method: "POST",
    body: payload,
    token,
  })
}

export function getPublicRooms(): Promise<PublicRoom[]> {
  return request("/api/rooms/public/")
}

export function searchContent(query: string, page = 1): Promise<SearchResult[]> {
  const params = new URLSearchParams({ q: query, page: String(page) })
  return request(`/api/rooms/search/?${params.toString()}`)
}

export function getRoomDetail(
  roomCode: string,
  token?: string | null
): Promise<RoomDetail> {
  return request(`/api/rooms/${roomCode}/detail/`, { token })
}

export function updateRoomSource(
  payload: {
    room_id: string
    provider: string
    video_id: string
  },
  token?: string | null
): Promise<{ room_id: string; video_provider: string; video_id: string }> {
  return request("/api/rooms/source/", {
    method: "POST",
    body: payload,
    token,
  })
}

export function getRoomParticipants(
  roomId: string,
  token?: string | null
): Promise<ParticipantRecord[]> {
  const params = new URLSearchParams({ room_id: roomId })
  return request(`/api/rooms/participants/?${params.toString()}`, { token })
}

export function resumeProgress(
  roomCode: string,
  token?: string | null
): Promise<{
  progress_percent: number
  last_position_seconds: number
  completed: boolean
}> {
  return request(`/api/rooms/${roomCode}/resume/`, { token })
}

export function saveProgress(
  payload: {
    room_id: string
    media_id: string
    media_type: string
    season?: number | null
    episode?: number | null
    timestamp: number
    duration: number
    progress_percent: number
    completed: boolean
  },
  token?: string | null
): Promise<unknown> {
  return request("/api/rooms/progress/save/", {
    method: "POST",
    body: payload,
    token,
  })
}

export function getProgress(
  payload: {
    room_id: string
    media_id: string
    media_type: string
  },
  token?: string | null
): Promise<unknown> {
  const params = new URLSearchParams({
    room_id: payload.room_id,
    media_id: payload.media_id,
    media_type: payload.media_type,
  })
  return request(`/api/rooms/progress/get/?${params.toString()}`, { token })
}
