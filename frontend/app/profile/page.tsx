"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { logout } from "@/lib/api"
import { loadLastRoomCode } from "@/lib/storage"
import { useSessionStore } from "@/store/sessionStore"

export default function ProfilePage() {
  const router = useRouter()
  const { user, hydrated, hydrate, clear } = useSessionStore()
  const [lastRoom, setLastRoom] = useState<string | null>(null)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  useEffect(() => {
    if (!hydrated) return
    setLastRoom(loadLastRoomCode())
  }, [hydrated])

  const handleLogout = async () => {
    try {
      await logout()
    } finally {
      clear()
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
                href="/"
                className="rounded-full border border-transparent px-3 py-1 transition hover:border-white/10 hover:bg-white/5"
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
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[color:var(--color-foreground)]"
              >
                Profile
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-xs">
            {user ? (
              <button onClick={handleLogout} className="btn btn-ghost">
                Logout
              </button>
            ) : (
              <Link href="/login" className="btn btn-outline">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-10">
        <section className="panel p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
            Profile
          </p>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold">
                {user ? user.display_name : "Guest viewer"}
              </h1>
              <p className="mt-1 text-sm text-[color:var(--color-muted)]">
                {user
                  ? user.is_guest
                    ? "Guest access"
                    : "Host access"
                  : "Sign in to access hosting tools"}
              </p>
            </div>
            {user ? (
              <span className="badge badge-muted">
                {user.is_guest ? "Guest" : "Host"}
              </span>
            ) : null}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="panel-soft p-6">
            <h2 className="text-lg font-semibold">Account status</h2>
            <p className="mt-2 text-sm text-[color:var(--color-muted)]">
              {user
                ? "Your session is active across devices. Use the dashboard to manage rooms."
                : "Sign in or continue as a guest to unlock live rooms."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="tag">Realtime sync</span>
              <span className="tag">Low latency</span>
              <span className="tag">Secure rooms</span>
            </div>
          </div>

          <div className="panel-soft p-6">
            <h2 className="text-lg font-semibold">Recent room</h2>
            <p className="mt-2 text-sm text-[color:var(--color-muted)]">
              {lastRoom
                ? "Jump back into your most recent stream room."
                : "No room history yet."}
            </p>
            {lastRoom ? (
              <button
                onClick={() => router.push(`/room/${lastRoom}`)}
                className="btn btn-outline mt-4"
              >
                Resume room {lastRoom}
              </button>
            ) : (
              <Link href="/" className="btn btn-outline mt-4">
                Browse streams
              </Link>
            )}
          </div>
        </section>

        <section className="panel p-6">
          <h2 className="text-lg font-semibold">Streaming preferences</h2>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Personalize your recommendations and notifications. Preferences are
            stored client side for now.
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="panel-outline px-4 py-3">
              <p className="text-xs text-[color:var(--color-muted)]">Notifications</p>
              <p className="mt-1 text-sm">Live room alerts enabled</p>
            </div>
            <div className="panel-outline px-4 py-3">
              <p className="text-xs text-[color:var(--color-muted)]">Theme</p>
              <p className="mt-1 text-sm">Dark streaming mode</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
