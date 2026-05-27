"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import {
  adminDeleteRoom,
  adminListRooms,
  adminToggleRoomChat,
  type AdminRoomRecord,
} from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Something went wrong"
}

function formatCount(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
  return value.toString()
}

function formatTimestamp(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

export default function AdminConsolePage() {
  const { user, token, hydrated, hydrate } = useSessionStore()

  const [rooms, setRooms] = useState<AdminRoomRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  const loadRooms = useCallback(async () => {
    if (!token) return

    setLoading(true)
    setError(null)
    try {
      const data = await adminListRooms(token)
      setRooms(data)
    } catch (err) {
      setRooms([])
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    if (!hydrated) return
    void loadRooms()
  }, [hydrated, loadRooms])

  const totalViewers = useMemo(
    () => rooms.reduce((sum, room) => sum + room.viewers, 0),
    [rooms]
  )

  const handleToggleChat = async (room: AdminRoomRecord) => {
    if (!token) return

    setActionError(null)
    try {
      const result = await adminToggleRoomChat(room.id, !room.is_chat_enabled, token)
      setRooms((current) =>
        current.map((item) =>
          item.id === room.id
            ? { ...item, is_chat_enabled: result.is_chat_enabled }
            : item
        )
      )
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

  const handleDeleteRoom = async (room: AdminRoomRecord) => {
    if (!token) return

    const ok = window.confirm(`Delete room ${room.code}?`)
    if (!ok) return

    setActionError(null)
    try {
      await adminDeleteRoom(room.id, token)
      setRooms((current) => current.filter((item) => item.id !== room.id))
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

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
                href="/dashboard"
                className="border border-transparent px-3 py-1 transition hover:border-white/10 hover:bg-white/5"
              >
                Dashboard
              </Link>
              <Link
                href="/admin-console"
                className="border border-white/10 bg-white/5 px-3 py-1 text-[color:var(--color-foreground)]"
              >
                Admin console
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-xs">
            {hydrated && user ? (
              <div className="flex items-center gap-2">
                <span className="badge badge-muted">
                  {user.is_guest ? "Guest" : "User"}
                </span>
                <span className="text-sm font-semibold">{user.display_name}</span>
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
            Admin
          </p>
          <h1 className="mt-3 text-2xl font-semibold">Room moderation</h1>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Staff-only console to manage room state and chat availability.
          </p>
        </section>

        {!token ? (
          <div className="panel-outline px-4 py-3 text-sm text-[color:var(--color-muted)]">
            Sign in to access the admin console.
          </div>
        ) : null}

        <section className="panel-soft p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-sm">
              <span className="badge badge-muted">Rooms {rooms.length}</span>
              <span className="badge badge-muted">
                Viewers {formatCount(totalViewers)}
              </span>
              {loading ? (
                <span className="text-xs text-[color:var(--color-muted)]">Loading…</span>
              ) : null}
            </div>
            <button onClick={loadRooms} className="btn btn-ghost" disabled={!token}>
              Refresh
            </button>
          </div>

          {error ? (
            <div className="mt-4 panel-outline px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          ) : null}
          {actionError ? (
            <div className="mt-4 panel-outline px-4 py-3 text-sm text-red-400">
              {actionError}
            </div>
          ) : null}

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.25em] text-[color:var(--color-muted)]">
                <tr className="border-b border-white/10">
                  <th className="py-3 pr-4">Code</th>
                  <th className="py-3 pr-4">Host</th>
                  <th className="py-3 pr-4">Genre</th>
                  <th className="py-3 pr-4">Viewers</th>
                  <th className="py-3 pr-4">State</th>
                  <th className="py-3 pr-4">Private</th>
                  <th className="py-3 pr-4">Chat</th>
                  <th className="py-3 pr-4">Created</th>
                  <th className="py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rooms.map((room) => (
                  <tr key={room.id} className="border-b border-white/5">
                    <td className="py-3 pr-4 font-semibold">{room.code}</td>
                    <td className="py-3 pr-4">{room.host}</td>
                    <td className="py-3 pr-4">{room.genre}</td>
                    <td className="py-3 pr-4">{formatCount(room.viewers)}</td>
                    <td className="py-3 pr-4">{room.state}</td>
                    <td className="py-3 pr-4">{room.is_private ? "Yes" : "No"}</td>
                    <td className="py-3 pr-4">
                      {room.is_chat_enabled ? "Enabled" : "Disabled"}
                    </td>
                    <td className="py-3 pr-4 text-xs text-[color:var(--color-muted)]">
                      {formatTimestamp(room.created_at)}
                    </td>
                    <td className="py-3">
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={() => handleToggleChat(room)}
                          className="btn btn-outline"
                        >
                          {room.is_chat_enabled ? "Disable chat" : "Enable chat"}
                        </button>
                        <button
                          onClick={() => handleDeleteRoom(room)}
                          className="btn btn-outline"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}

                {!loading && token && rooms.length === 0 ? (
                  <tr>
                    <td
                      colSpan={9}
                      className="py-6 text-sm text-[color:var(--color-muted)]"
                    >
                      No rooms found.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  )
}
