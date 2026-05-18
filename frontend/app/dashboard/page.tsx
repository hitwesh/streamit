"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  createRoom,
  getPublicRooms,
  joinRoom,
  type PublicRoom,
} from "@/lib/api"
import { loadLastRoomCode, saveRoomMeta } from "@/lib/storage"
import { useSessionStore } from "@/store/sessionStore"

const DEFAULT_ENTRY_MODE = "APPROVAL"

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Something went wrong"
}

function formatCount(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
  return value.toString()
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, token, hydrated, hydrate } = useSessionStore()

  const [isPrivate, setIsPrivate] = useState(false)
  const [entryMode, setEntryMode] = useState<string>(DEFAULT_ENTRY_MODE)
  const [joinCode, setJoinCode] = useState("")
  const [joinPassword, setJoinPassword] = useState("")
  const [createError, setCreateError] = useState<string | null>(null)
  const [joinError, setJoinError] = useState<string | null>(null)
  const [joinStatus, setJoinStatus] = useState<string | null>(null)
  const [publicRooms, setPublicRooms] = useState<PublicRoom[]>([])
  const [publicLoading, setPublicLoading] = useState(false)
  const [publicError, setPublicError] = useState<string | null>(null)
  const [lastRoom, setLastRoom] = useState<string | null>(null)

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

  const totalViewers = useMemo(
    () => publicRooms.reduce((sum, room) => sum + room.viewers, 0),
    [publicRooms]
  )

  const handleCreateRoom = async () => {
    setCreateError(null)

    if (!user || user.is_guest) {
      setCreateError("Host login required to create a room")
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

  const handleJoinRoom = async () => {
    setJoinError(null)
    setJoinStatus(null)

    if (!token || !user) {
      setJoinError("Sign in or use guest access to join a room")
      return
    }

    const code = joinCode.trim().toUpperCase()
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

  const canCreate = Boolean(user && token && !user.is_guest)
  const canJoin = Boolean(user && token)

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/5 bg-black/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <Link
              href="/"
              className="text-sm font-semibold uppercase tracking-[0.4em] text-white"
            >
              StreamIt
            </Link>
            <nav className="hidden md:flex items-center gap-2 text-xs text-[color:var(--color-muted)]">
              <Link
                href="/"
                className="rounded-full border border-transparent px-3 py-1 transition hover:border-white/10 hover:bg-white/5"
              >
                Discover
              </Link>
              <Link
                href="/dashboard"
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[color:var(--color-foreground)]"
              >
                Dashboard
              </Link>
              <Link
                href="/profile"
                className="rounded-full border border-transparent px-3 py-1 transition hover:border-white/10 hover:bg-white/5"
              >
                Profile
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-xs">
            {user ? (
              <div className="flex items-center gap-2">
                <span className="badge badge-muted">
                  {user.is_guest ? "Guest" : "Host"}
                </span>
                <span className="text-sm font-semibold">
                  {user.display_name}
                </span>
              </div>
            ) : (
              <Link href="/login" className="btn btn-outline">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-8">
        <section className="panel p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
            Creator studio
          </p>
          <h1 className="mt-3 text-2xl font-semibold">
            Streaming control center.
          </h1>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Manage private rooms, approvals, and live sessions from a single
            workspace.
          </p>
        </section>

        {!user ? (
          <div className="panel-outline px-4 py-3 text-sm text-[color:var(--color-muted)]">
            Sign in to create or join rooms. Guest access is available on the
            login page.
          </div>
        ) : null}

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="panel-soft p-4">
            <p className="text-xs text-[color:var(--color-muted)]">Live rooms</p>
            <p className="mt-2 text-xl font-semibold">{publicRooms.length}</p>
          </div>
          <div className="panel-soft p-4">
            <p className="text-xs text-[color:var(--color-muted)]">Viewers online</p>
            <p className="mt-2 text-xl font-semibold">{formatCount(totalViewers)}</p>
          </div>
          <div className="panel-soft p-4">
            <p className="text-xs text-[color:var(--color-muted)]">Last room</p>
            <p className="mt-2 text-xl font-semibold">
              {lastRoom ? lastRoom : "None yet"}
            </p>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="panel p-6">
            <h2 className="text-lg font-semibold">Create a room</h2>
            <p className="mt-1 text-sm text-[color:var(--color-muted)]">
              Launch public or private rooms with approvals and host controls.
            </p>
            <div className="mt-4 grid gap-4">
              <div className="panel-soft p-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={isPrivate}
                    onChange={(event) => setIsPrivate(event.target.checked)}
                    className="accent-[color:var(--color-accent)]"
                  />
                  Private room
                </label>
                <div className="mt-3 flex flex-col gap-2 text-sm">
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
              {createError ? (
                <p className="text-xs text-red-400">{createError}</p>
              ) : null}
              <button
                onClick={handleCreateRoom}
                className="btn btn-primary"
                disabled={!canCreate}
              >
                Create room
              </button>
              {!canCreate ? (
                <p className="text-xs text-[color:var(--color-muted)]">
                  Host access is required to create rooms.
                </p>
              ) : null}
            </div>
          </div>

          <div className="panel p-6">
            <h2 className="text-lg font-semibold">Join a room</h2>
            <p className="mt-1 text-sm text-[color:var(--color-muted)]">
              Jump into a room using a share code or invite password.
            </p>
            <div className="mt-4 space-y-3">
              <input
                value={joinCode}
                onChange={(event) => setJoinCode(event.target.value)}
                placeholder="Room code"
                className="input"
              />
              <input
                value={joinPassword}
                onChange={(event) => setJoinPassword(event.target.value)}
                placeholder="Room password (optional)"
                className="input"
              />
              {joinError ? (
                <p className="text-xs text-red-400">{joinError}</p>
              ) : null}
              {joinStatus ? (
                <p className="text-xs text-[color:var(--color-muted)]">
                  {joinStatus}
                </p>
              ) : null}
              <button
                onClick={handleJoinRoom}
                className="btn btn-outline"
                disabled={!canJoin}
              >
                Join room
              </button>
              {!canJoin ? (
                <p className="text-xs text-[color:var(--color-muted)]">
                  Sign in to join rooms or use guest access.
                </p>
              ) : null}
            </div>
          </div>
        </section>

        <section className="panel-soft p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Live room overview</h2>
            <button onClick={loadPublicRooms} className="btn btn-ghost">
              Refresh
            </button>
          </div>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Total viewers across public rooms. Use this to gauge activity before
            going live.
          </p>
          <div className="mt-4 flex items-center gap-4 text-sm">
            <span className="badge badge-muted">Rooms {publicRooms.length}</span>
            <span className="badge badge-muted">
              Viewers {formatCount(totalViewers)}
            </span>
            {publicLoading ? (
              <span className="text-xs text-[color:var(--color-muted)]">
                Loading...
              </span>
            ) : null}
          </div>
          {publicError ? (
            <p className="mt-3 text-xs text-red-400">{publicError}</p>
          ) : null}
          {lastRoom ? (
            <div className="mt-4">
              <button
                onClick={() => router.push(`/room/${lastRoom}`)}
                className="btn btn-outline"
              >
                Resume room {lastRoom}
              </button>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  )
}
