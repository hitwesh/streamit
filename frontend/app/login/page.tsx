"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { guestLogin, login } from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Something went wrong"
}

export default function LoginPage() {
  const router = useRouter()
  const { hydrate, setSession, user, hydrated } = useSessionStore()

  const [loginEmail, setLoginEmail] = useState("")
  const [loginPassword, setLoginPassword] = useState("")
  const [guestName, setGuestName] = useState("")
  const [loginError, setLoginError] = useState<string | null>(null)
  const [guestError, setGuestError] = useState<string | null>(null)

  useEffect(() => {
    hydrate()
  }, [hydrate])

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
      router.push("/dashboard")
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
      router.push("/dashboard")
    } catch (error) {
      setGuestError(getErrorMessage(error))
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/5 bg-black/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <Link
            href="/"
            className="text-sm font-semibold uppercase tracking-[0.4em] text-white"
          >
            StreamIt
          </Link>
          <div className="flex items-center gap-3 text-xs">
            <Link href="/signup" className="btn btn-outline">
              Create account
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-5xl gap-6 px-6 py-10 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="panel p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
            Host login
          </p>
          <h1 className="mt-3 text-2xl font-semibold">
            Welcome back to StreamIt.
          </h1>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Sign in to create rooms, manage approvals, and broadcast live watch
            parties.
          </p>

          <div className="mt-6 space-y-3">
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
              <p className="text-xs text-red-400">{loginError}</p>
            ) : null}
            <button onClick={handleLogin} className="btn btn-primary w-full">
              Sign in
            </button>
          </div>

          <div className="mt-6 flex items-center justify-between text-xs text-[color:var(--color-muted)]">
            <span>Need an account?</span>
            <Link href="/signup" className="btn btn-link">
              Request access
            </Link>
          </div>
        </section>

        <section className="panel-soft p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
            Guest access
          </p>
          <h2 className="mt-3 text-lg font-semibold">
            Jump in without an account.
          </h2>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Join public rooms and experience the live sync. Guest sessions are
            fast and still fully synchronized.
          </p>

          <div className="mt-6 space-y-3">
            <input
              value={guestName}
              onChange={(event) => setGuestName(event.target.value)}
              placeholder="Display name"
              className="input"
            />
            {guestError ? (
              <p className="text-xs text-red-400">{guestError}</p>
            ) : null}
            <button onClick={handleGuestLogin} className="btn btn-outline w-full">
              Continue as guest
            </button>
          </div>

          {hydrated && user ? (
            <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-[color:var(--color-muted)]">
              You are already signed in as {user.display_name}. You can head to
              your dashboard to continue.
            </div>
          ) : null}
        </section>
      </main>
    </div>
  )
}
