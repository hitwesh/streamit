"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { getPublicRooms, joinRoom, logout, type PublicRoom } from "@/lib/api"
import { loadLastRoomCode, saveRoomMeta } from "@/lib/storage"
import { useSessionStore } from "@/store/sessionStore"

const CATEGORIES = [
  { name: "Watch parties", live: 18 },
  { name: "Movies", live: 12 },
  { name: "Series", live: 8 },
  { name: "Anime", live: 6 },
  { name: "Sports", live: 9 },
  { name: "Music", live: 5 },
  { name: "Documentary", live: 4 },
  { name: "Indie", live: 7 },
]

const TRENDING = [
  {
    title: "Low latency rooms",
    detail: "Sync drift under two seconds",
  },
  {
    title: "Creator watch lists",
    detail: "Curated community programming",
  },
  {
    title: "Co-stream sessions",
    detail: "Multi-host live watch parties",
  },
]

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Something went wrong"
}

function formatCount(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
  return value.toString()
}

function formatAge(timestamp: string): string {
  const parsed = Date.parse(timestamp)
  if (Number.isNaN(parsed)) return "Just now"
  const diffMinutes = Math.floor((Date.now() - parsed) / 60000)
  if (diffMinutes < 1) return "Just now"
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  const hours = Math.floor(diffMinutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export default function Home() {
  const router = useRouter()
  const { user, token, hydrated, hydrate, clear } = useSessionStore()

  const [publicRooms, setPublicRooms] = useState<PublicRoom[]>([])
  const [publicLoading, setPublicLoading] = useState(false)
  const [publicError, setPublicError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [lastRoom, setLastRoom] = useState<string | null>(null)
  const [joinError, setJoinError] = useState<string | null>(null)
  const [joinStatus, setJoinStatus] = useState<string | null>(null)

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

  const filteredRooms = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    if (!term) return publicRooms
    return publicRooms.filter(
      (room) =>
        room.code.toLowerCase().includes(term) ||
        room.host.toLowerCase().includes(term)
    )
  }, [publicRooms, searchTerm])

  const featuredRoom = filteredRooms[0] ?? null
  const visibleRooms = filteredRooms.slice(0, 6)
  const totalViewers = useMemo(
    () => publicRooms.reduce((sum, room) => sum + room.viewers, 0),
    [publicRooms]
  )

  const handleJoinRoom = async (roomCode: string) => {
    setJoinError(null)
    setJoinStatus(null)

    if (!token || !user) {
      router.push("/login")
      return
    }

    try {
      const data = await joinRoom({ code: roomCode }, token)

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

  const handleLogout = async () => {
    try {
      await logout()
    } finally {
      clear()
    }
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-white/5 bg-black/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4">
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
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[color:var(--color-foreground)]"
              >
                Discover
              </Link>
              <Link
                href="/dashboard"
                className="rounded-full border border-transparent px-3 py-1 transition hover:border-white/10 hover:bg-white/5"
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
          <div className="hidden lg:flex items-center gap-3">
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search live streams"
              className="input w-72"
            />
            <button onClick={loadPublicRooms} className="btn btn-ghost">
              Refresh
            </button>
          </div>
          <div className="flex items-center gap-3 text-xs">
            {hydrated && user ? (
              <>
                <div className="hidden sm:flex flex-col items-end">
                  <span className="text-[10px] uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
                    Session
                  </span>
                  <span className="text-sm font-semibold text-[color:var(--color-foreground)]">
                    {user.display_name}
                  </span>
                </div>
                <button onClick={handleLogout} className="btn btn-ghost">
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="btn btn-outline">
                  Sign in
                </Link>
                <Link href="/signup" className="btn btn-primary">
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="mx-auto grid w-full max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="hidden lg:flex flex-col gap-4">
          <div className="panel-soft p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
              Navigation
            </p>
            <div className="mt-4 flex flex-col gap-2 text-sm">
              <Link
                href="/"
                className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-[color:var(--color-foreground)]"
              >
                Discover
              </Link>
              <Link
                href="/dashboard"
                className="rounded-2xl border border-transparent px-3 py-2 transition hover:border-white/10 hover:bg-white/5"
              >
                Creator studio
              </Link>
              <Link
                href="/profile"
                className="rounded-2xl border border-transparent px-3 py-2 transition hover:border-white/10 hover:bg-white/5"
              >
                Profile
              </Link>
              <Link
                href="/login"
                className="rounded-2xl border border-transparent px-3 py-2 transition hover:border-white/10 hover:bg-white/5"
              >
                Sign in
              </Link>
            </div>
          </div>

          <div className="panel-soft p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
              Categories
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {CATEGORIES.map((category) => (
                <span key={category.name} className="tag">
                  {category.name} ({category.live})
                </span>
              ))}
            </div>
          </div>
        </aside>

        <main className="flex flex-col gap-8">
          <div className="panel-soft p-4 lg:hidden">
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search live streams"
              className="input"
            />
          </div>

          {joinError ? (
            <div className="panel-outline px-4 py-3 text-sm text-red-400">
              {joinError}
            </div>
          ) : null}
          {joinStatus ? (
            <div className="panel-outline px-4 py-3 text-sm text-[color:var(--color-muted)]">
              {joinStatus}
            </div>
          ) : null}

          <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="panel p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="badge">Live</span>
                  <span className="text-xs text-[color:var(--color-muted)]">
                    Featured stream
                  </span>
                </div>
                <span className="text-xs text-[color:var(--color-muted)]">
                  {publicRooms.length} live now
                </span>
              </div>
              <div className="mt-4 overflow-hidden rounded-2xl">
                {featuredRoom ? (
                  <div className="relative aspect-video stream-thumb">
                    <div className="absolute inset-0 flex flex-col justify-between bg-black/40 p-4">
                      <div className="flex items-center gap-2 text-xs">
                        <span className="badge">Live</span>
                        <span className="badge badge-muted">
                          {formatCount(featuredRoom.viewers)} viewers
                        </span>
                      </div>
                      <div>
                        <h2 className="text-xl font-semibold">
                          {featuredRoom.host}
                        </h2>
                        <p className="text-sm text-[color:var(--color-muted)]">
                          Room {featuredRoom.code} - started {formatAge(featuredRoom.created_at)}
                        </p>
                        <div className="mt-4 flex flex-wrap gap-3">
                          <button
                            onClick={() => handleJoinRoom(featuredRoom.code)}
                            className="btn btn-primary"
                          >
                            Watch now
                          </button>
                          <button
                            onClick={() => router.push("/dashboard")}
                            className="btn btn-outline"
                          >
                            Host a room
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex aspect-video items-center justify-center rounded-2xl border border-white/10 bg-black/60 text-sm text-[color:var(--color-muted)]">
                    No featured streams yet.
                  </div>
                )}
              </div>
            </div>

            <div className="panel-soft p-5">
              <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
                Discover
              </p>
              <h3 className="mt-3 text-lg font-semibold">
                Premium watch parties, live and on demand.
              </h3>
              <p className="mt-2 text-sm text-[color:var(--color-muted)]">
                Join public rooms or launch a private stream with approvals and
                real time sync. The homepage stays focused on content, so you
                can explore before you sign in.
              </p>
              <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
                <div className="panel-outline px-3 py-3">
                  <p className="text-xs text-[color:var(--color-muted)]">Live rooms</p>
                  <p className="mt-1 text-lg font-semibold">
                    {publicRooms.length}
                  </p>
                </div>
                <div className="panel-outline px-3 py-3">
                  <p className="text-xs text-[color:var(--color-muted)]">Viewers online</p>
                  <p className="mt-1 text-lg font-semibold">
                    {formatCount(totalViewers)}
                  </p>
                </div>
              </div>
              <div className="mt-5 flex flex-col gap-3">
                <Link href="/dashboard" className="btn btn-primary w-full">
                  Open creator studio
                </Link>
                {lastRoom ? (
                  <button
                    onClick={() => router.push(`/room/${lastRoom}`)}
                    className="btn btn-outline w-full"
                  >
                    Resume room {lastRoom}
                  </button>
                ) : (
                  <div className="text-xs text-[color:var(--color-muted)]">
                    No recent room history yet.
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Live now</h2>
              <button onClick={loadPublicRooms} className="btn btn-ghost">
                Refresh
              </button>
            </div>
            {publicLoading ? (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {Array.from({ length: 6 }).map((_, index) => (
                  <div key={index} className="stream-card">
                    <div className="aspect-video skeleton" />
                    <div className="space-y-3 p-4">
                      <div className="h-3 w-24 rounded-full skeleton" />
                      <div className="h-4 w-40 rounded-full skeleton" />
                      <div className="h-3 w-20 rounded-full skeleton" />
                    </div>
                  </div>
                ))}
              </div>
            ) : visibleRooms.length === 0 ? (
              <div className="panel-outline px-4 py-6 text-sm text-[color:var(--color-muted)]">
                No public rooms are live right now. Check back soon or start one
                from your dashboard.
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {visibleRooms.map((room) => (
                  <div key={room.code} className="stream-card">
                    <div className="relative aspect-video stream-thumb">
                      <div className="absolute left-3 top-3 flex items-center gap-2">
                        <span className="badge">Live</span>
                        <span className="badge badge-muted">
                          {formatCount(room.viewers)} watching
                        </span>
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="text-base font-semibold">
                        {room.host}
                      </h3>
                      <p className="text-xs text-[color:var(--color-muted)]">
                        Room {room.code} - started {formatAge(room.created_at)}
                      </p>
                      <div className="mt-4 flex items-center justify-between">
                        <button
                          onClick={() => handleJoinRoom(room.code)}
                          className="btn btn-primary"
                        >
                          Watch
                        </button>
                        <span className="text-xs text-[color:var(--color-muted)]">
                          {formatCount(room.viewers)} viewers
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {publicError ? (
              <div className="panel-outline px-4 py-3 text-sm text-red-400">
                {publicError}
              </div>
            ) : null}
          </section>

          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Browse categories</h2>
              <span className="text-xs text-[color:var(--color-muted)]">
                Updated hourly
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map((category) => (
                <span key={category.name} className="tag">
                  {category.name} ({category.live} live)
                </span>
              ))}
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            {TRENDING.map((item) => (
              <div key={item.title} className="panel-soft p-4">
                <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--color-muted)]">
                  Trending
                </p>
                <h3 className="mt-3 text-base font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm text-[color:var(--color-muted)]">
                  {item.detail}
                </p>
              </div>
            ))}
          </section>
        </main>
      </div>
    </div>
  )
}
