"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  createRoom,
  guestLogin,
  joinRoom,
  login,
  logout,
  getPublicRooms,
  type PublicRoom,
} from "@/lib/api"
import { loadLastRoomCode, saveRoomMeta } from "@/lib/storage"
import { useSessionStore } from "@/store/sessionStore"

const DEFAULT_ENTRY_MODE = "APPROVAL"

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Something went wrong"
}

export default function Home() {
  const router = useRouter()
  const { user, token, hydrated, hydrate, setSession, clear } = useSessionStore()

  const [loginEmail, setLoginEmail] = useState("")
  const [loginPassword, setLoginPassword] = useState("")
  const [guestName, setGuestName] = useState("")
  const [joinCode, setJoinCode] = useState("")
  const [joinPassword, setJoinPassword] = useState("")
  const [isPrivate, setIsPrivate] = useState(false)
  const [entryMode, setEntryMode] = useState<string>(DEFAULT_ENTRY_MODE)
  const [publicRooms, setPublicRooms] = useState<PublicRoom[]>([])
  const [publicLoading, setPublicLoading] = useState(false)
  const [lastRoom, setLastRoom] = useState<string | null>(null)

  const [loginError, setLoginError] = useState<string | null>(null)
  const [guestError, setGuestError] = useState<string | null>(null)
  const [createError, setCreateError] = useState<string | null>(null)
  const [joinError, setJoinError] = useState<string | null>(null)
  const [joinStatus, setJoinStatus] = useState<string | null>(null)
  const [publicError, setPublicError] = useState<string | null>(null)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  useEffect(() => {
    if (!hydrated) return
    setLastRoom(loadLastRoomCode())
  }, [hydrated])

  const loadPublicRooms = async () => {
    setPublicLoading(true)
    setPublicError(null)
    try {
      const data = await getPublicRooms()
      setPublicRooms(data)
    } catch (error) {
      setPublicRooms([])
      setPublicError(getErrorMessage(error))
    } finally {
      setPublicLoading(false)
    }
  }

  useEffect(() => {
    if (!hydrated) return
    void loadPublicRooms()
  }, [hydrated])

  const handleLogin = async () => {
    setLoginError(null)

    if (!loginEmail.trim() || !loginPassword.trim()) {
      setLoginError("Email and password required")
      return
    }

    try {
      const data = await login(loginEmail, loginPassword)
      setSession(
        {
          id: data.id,
          display_name: data.display_name,
          is_guest: data.is_guest,
        },
        data.access_token
      )
    } catch (error) {
      setLoginError(getErrorMessage(error))
    }
  }

  const handleGuestLogin = async () => {
    setGuestError(null)

    if (!guestName.trim()) {
      setGuestError("Display name required")
      return
    }

    try {
      const data = await guestLogin(guestName)
      setSession(
        {
          id: data.id,
          display_name: data.display_name,
          is_guest: data.is_guest,
        },
        data.access_token
      )
    } catch (error) {
      setGuestError(getErrorMessage(error))
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
    } finally {
      clear()
    }
  }

  const handleCreateRoom = async () => {
    setCreateError(null)

    if (!user || user.is_guest) {
      setCreateError("Login required to host a room")
      return
    }

    try {
      const payload = {
        is_private: isPrivate,
        entry_mode: isPrivate ? entryMode : null,
      }
      const data = await createRoom(payload, token)

      saveRoomMeta({
        room_id: data.room_id,
        code: data.code,
        status: "APPROVED",
        is_host: true,
        entry_mode: data.entry_mode,
        is_private: data.is_private,
        room_password: data.room_password,
      })

      router.push(`/room/${data.code}`)
    } catch (error) {
      setCreateError(getErrorMessage(error))
    }
  }

  const handleJoinRoom = async (codeOverride?: string) => {
    setJoinError(null)
    setJoinStatus(null)

    if (!token || !user) {
      setJoinError("Login or guest login required")
      return
    }

    const code = (codeOverride ?? joinCode).trim().toUpperCase()
    if (!code) {
      setJoinError("Room code required")
      return
    }

    try {
      const data = await joinRoom(
        {
          code,
          password: joinPassword || undefined,
        },
        token
      )

      saveRoomMeta({
        room_id: data.room_id,
        code: data.code,
        status: data.status,
        is_host: data.is_host,
      })

      if (data.status === "PENDING") {
        setJoinStatus("Pending approval from host")
        return
      }

      router.push(`/room/${data.code}`)
    } catch (error) {
      setJoinError(getErrorMessage(error))
    }
  }

  return (
    <div className="min-h-screen px-6 py-10">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        <header className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="animate-rise">
            <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
              StreamIt
            </p>
            <h1 className="mt-3 text-3xl font-semibold text-[color:var(--color-foreground)] md:text-4xl">
              Realtime rooms for synchronized playback.
            </h1>
            <p className="mt-3 max-w-xl text-sm text-[color:var(--color-muted)]">
              Host a private room, approve guests, and keep everyone in sync with
              authoritative playback state. Guests can join instantly and chat
              without leaving the stream.
            </p>
          </div>
          <div className="panel-soft flex items-center gap-4 px-4 py-3 text-sm">
            {hydrated && user ? (
              <>
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-[color:var(--color-muted)]">
                    Session
                  </p>
                  <p className="text-sm font-semibold text-[color:var(--color-foreground)]">
                    {user.display_name}
                  </p>
                  <p className="text-xs text-[color:var(--color-muted)]">
                    {user.is_guest ? "Guest" : "Host"}
                  </p>
                </div>
                <button onClick={handleLogout} className="btn btn-outline">
                  Logout
                </button>
              </>
            ) : (
              <p className="text-xs text-[color:var(--color-muted)]">
                Login to create or join rooms.
              </p>
            )}
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="flex flex-col gap-6">
            <section className="panel animate-rise p-6">
              <h2 className="text-lg font-semibold">Session</h2>
              <p className="mt-1 text-sm text-[color:var(--color-muted)]">
                Use a host account to create rooms or guest login to join.
              </p>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="panel-soft flex flex-col gap-3 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-[color:var(--color-muted)]">
                    Host login
                  </p>
                  <input
                    value={loginEmail}
                    onChange={(event) => setLoginEmail(event.target.value)}
                    placeholder="Email"
                    className="input"
                  />
                  <input
                    value={loginPassword}
                    onChange={(event) => setLoginPassword(event.target.value)}
                    placeholder="Password"
                    type="password"
                    className="input"
                  />
                  {loginError ? (
                    <p className="text-xs text-red-600">{loginError}</p>
                  ) : null}
                  <button onClick={handleLogin} className="btn btn-primary">
                    Login
                  </button>
                </div>
                <div className="panel-soft flex flex-col gap-3 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-[color:var(--color-muted)]">
                    Guest login
                  </p>
                  <input
                    value={guestName}
                    onChange={(event) => setGuestName(event.target.value)}
                    placeholder="Display name"
                    className="input"
                  />
                  {guestError ? (
                    <p className="text-xs text-red-600">{guestError}</p>
                  ) : null}
                  <button onClick={handleGuestLogin} className="btn btn-outline">
                    Continue as guest
                  </button>
                </div>
              </div>
            </section>

            <section className="panel animate-rise animate-delay-1 p-6">
              <h2 className="text-lg font-semibold">Create room</h2>
              <p className="mt-1 text-sm text-[color:var(--color-muted)]">
                Hosts can create public rooms or private rooms with approvals.
              </p>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="panel-soft flex flex-col gap-3 p-4">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={isPrivate}
                      onChange={(event) => setIsPrivate(event.target.checked)}
                      className="accent-[color:var(--color-accent)]"
                    />
                    Private room
                  </label>
                  <div className="flex flex-col gap-2 text-sm">
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="entry-mode"
                        checked={entryMode === "APPROVAL"}
                        onChange={() => setEntryMode("APPROVAL")}
                        className="accent-[color:var(--color-accent)]"
                        disabled={!isPrivate}
                      />
                      Approval required
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="entry-mode"
                        checked={entryMode === "PASSWORD"}
                        onChange={() => setEntryMode("PASSWORD")}
                        className="accent-[color:var(--color-accent)]"
                        disabled={!isPrivate}
                      />
                      Password protected
                    </label>
                  </div>
                </div>
                <div className="panel-soft flex flex-col gap-3 p-4">
                  <p className="text-sm text-[color:var(--color-muted)]">
                    Private rooms can share a password once created. Guests are
                    auto-approved for public rooms.
                  </p>
                  {createError ? (
                    <p className="text-xs text-red-600">{createError}</p>
                  ) : null}
                  <button onClick={handleCreateRoom} className="btn btn-primary">
                    Create room
                  </button>
                </div>
              </div>
            </section>
          </div>

          <div className="flex flex-col gap-6">
            <section className="panel animate-rise animate-delay-2 p-6">
              <h2 className="text-lg font-semibold">Join room</h2>
              <p className="mt-1 text-sm text-[color:var(--color-muted)]">
                Enter a room code or jump into a public room below.
              </p>
              <div className="mt-4 flex flex-col gap-3">
                <input
                  value={joinCode}
                  onChange={(event) => setJoinCode(event.target.value)}
                  placeholder="Room code"
                  className="input"
                />
                <input
                  value={joinPassword}
                  onChange={(event) => setJoinPassword(event.target.value)}
                  placeholder="Room password (if required)"
                  className="input"
                />
                {joinError ? (
                  <p className="text-xs text-red-600">{joinError}</p>
                ) : null}
                {joinStatus ? (
                  <p className="text-xs text-[color:var(--color-muted)]">
                    {joinStatus}
                  </p>
                ) : null}
                <div className="flex flex-wrap gap-3">
                  <button onClick={() => handleJoinRoom()} className="btn btn-primary">
                    Join room
                  </button>
                  {lastRoom ? (
                    <button
                      onClick={() => router.push(`/room/${lastRoom}`)}
                      className="btn btn-outline"
                    >
                      Open last room
                    </button>
                  ) : null}
                </div>
              </div>
            </section>

            <section className="panel animate-rise animate-delay-3 p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Public rooms</h2>
                <button onClick={loadPublicRooms} className="btn btn-ghost">
                  Refresh
                </button>
              </div>
              <p className="mt-1 text-sm text-[color:var(--color-muted)]">
                Viewers only count active sockets connected to the room.
              </p>
              <div className="mt-4 flex flex-col gap-3">
                {publicLoading ? (
                  <p className="text-sm text-[color:var(--color-muted)]">
                    Loading rooms...
                  </p>
                ) : publicRooms.length === 0 ? (
                  <p className="text-sm text-[color:var(--color-muted)]">
                    No public rooms right now.
                  </p>
                ) : (
                  publicRooms.map((room) => (
                    <div
                      key={room.code}
                      className="flex items-center justify-between rounded-2xl border border-black/5 bg-white/70 px-3 py-3"
                    >
                      <div>
                        <p className="text-sm font-semibold text-[color:var(--color-foreground)]">
                          {room.code}
                        </p>
                        <p className="text-xs text-[color:var(--color-muted)]">
                          Host {room.host} - {room.viewers} viewers
                        </p>
                      </div>
                      <button
                        onClick={() => handleJoinRoom(room.code)}
                        className="btn btn-outline"
                      >
                        Join
                      </button>
                    </div>
                  ))
                )}
                {publicError ? (
                  <p className="text-xs text-red-600">{publicError}</p>
                ) : null}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}
